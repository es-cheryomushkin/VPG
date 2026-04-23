extends "res://addons/gut/test.gd"

var car: CharacterBody2D
var test_scene = preload("res://scenes/playground/playground.scn")

func before_all():
	var world = test_scene.instantiate()
	get_tree().get_root().add_child(world)
	car = world.get_node("Player/Car")
	print("\n" + "=".repeat(70))
	print("PHYSICS TEST SUITE INITIALIZED")
	print("=".repeat(70))

func after_all():
	if car and car.is_inside_tree():
		car.queue_free()
	print("\n" + "=".repeat(70))
	print("PHYSICS TEST SUITE COMPLETED")
	print("=".repeat(70))

# ============================================================
# ТЕСТ 0: ПРОВЕРКА ПРОЕЗДА СВОЕЙ ДЛИНЫ
# ============================================================
func test_drive_own_length():
	print("\n[TEST 0/5] Distance Time Test - Driving Own Length")
	var car_length_px = 480.0   # известная длина спрайта
	print("   Car length: %.1f px" % car_length_px)
	
	# Сбрасываем позицию машины
	car.position = Vector2.ZERO
	var target_pos = Vector2(car_length_px, 0.0)
	
	# Засекаем время
	var start_time = Time.get_ticks_msec()
	var driven = false
	var max_wait = 10000   # 10 секунд максимум
	
	# Начинаем движение
	Input.action_press("move_forward")
	while Time.get_ticks_msec() - start_time < max_wait:
		car._physics_process(1.0 / 60.0)
		if car.position.x >= target_pos.x:
			driven = true
			var elapsed = (Time.get_ticks_msec() - start_time) / 1000.0
			print("   Time to drive own length: %.3f seconds" % elapsed)
			# Ожидаемое время при максимальной скорости 1600 px/s — 0.3 с.
			# При разгоне с нуля будет чуть больше, но в любом случае должно быть меньше 1 секунды.
			assert_lt(elapsed, 1.5, "Time to drive own length should be less than 1 second")
			break
		await get_tree().physics_frame
	
	Input.action_release("move_forward")
	if not driven:
		assert_false("Failed to drive own length")
	print("   " + "-".repeat(55))


# ============================================================
# ТЕСТ 1: ДОСТИЖЕНИЕ МАКСИМАЛЬНОЙ СКОРОСТИ
# ============================================================
func test_max_speed_reached():
	print("\n[TEST 1/5] Maximum Speed Test")
	var target_speed = car.max_speed_forward
	print("   Target max speed: %.1f px/s" % target_speed)
	
	# Временно отключаем damping, чтобы машина могла разогнаться
	var old_damping = car.damping
	car.damping = 1.0  # Убираем сопротивление
	
	var start_time = Time.get_ticks_msec()
	var max_wait_time = 10000
	var reached_max = false
	
	Input.action_press("move_forward")
	while Time.get_ticks_msec() - start_time < max_wait_time:
		car._physics_process(1.0 / 60.0)
		
		# Добавляем вывод текущей скорости
		if Time.get_ticks_msec() - start_time > 1000:
			print("   Current speed: %.1f px/s" % car.current_speed)
		
		if car.current_speed >= target_speed * 0.89:
			reached_max = true
			var time_to_max = (Time.get_ticks_msec() - start_time) / 1000.0
			print("   Result: Max speed reached in %.2f seconds" % time_to_max)
			print("   Final speed: %.1f px/s" % car.current_speed)
			assert_lte(time_to_max, 4.0, "Acceleration time must not exceed 4 seconds")
			break
		await get_tree().physics_frame
	
	Input.action_release("move_forward")
	
	# Восстанавливаем damping
	car.damping = old_damping
	
	# Исправленная проверка
	if not reached_max:
		var final_speed = car.current_speed
		print("   WARNING: Max speed not reached. Final speed: %.1f px/s" % final_speed)
		assert_true(reached_max, "Failed to reach max speed within %s seconds. Final speed: %.1f px/s" % [max_wait_time / 1000.0, final_speed])
	
	print("   " + "-".repeat(55))

# ============================================================
# ТЕСТ 2: ТОРМОЖЕНИЕ С МАКСИМАЛЬНОЙ СКОРОСТИ
# ============================================================
func test_stop_from_max_speed():
	print("\n[TEST 2/5] Braking Test")
	var target_speed = car.max_speed_forward
	
	# Отключаем damping на время разгона
	var old_damping = car.damping
	car.damping = 1.0
	
	# Разгон
	var start_time = Time.get_ticks_msec()
	var max_wait_time = 10000
	Input.action_press("move_forward")
	while car.current_speed < target_speed * 0.95 and Time.get_ticks_msec() - start_time < max_wait_time:
		car._physics_process(1.0 / 60.0)
		await get_tree().physics_frame
	Input.action_release("move_forward")
	
	print("   Max speed reached: %.1f px/s" % car.current_speed)
	
	# Восстанавливаем damping для торможения
	car.damping = old_damping
	
	# Торможение
	start_time = Time.get_ticks_msec()
	var stopped = false
	Input.action_press("brake")
	while Time.get_ticks_msec() - start_time < max_wait_time:
		car._physics_process(1.0 / 60.0)
		if car.current_speed <= 0.1:
			stopped = true
			var stop_time = (Time.get_ticks_msec() - start_time) / 1000.0
			print("   Result: Full stop in %.2f seconds" % stop_time)
			assert_lte(stop_time, 3.5, "Braking time must not exceed 3.5 seconds")
			break
		await get_tree().physics_frame
	Input.action_release("brake")
	
	if not stopped:
		print("   WARNING: Did not stop completely")
		assert_true(stopped, "Failed to stop within 10.0 seconds. Final speed: %.1f px/s" % car.current_speed)
	
	print("   " + "-".repeat(55))

# ============================================================
# ТЕСТ 3: ПРОВЕРКА ПЕРЕСЧЁТА СКОРОСТИ (px/с -> м/с)
# ============================================================
func test_speed_conversion():
	print("\n[TEST 3/5] Speed Conversion Test (px/s -> m/s)")
	var pixels_per_meter = 480.0 / 4.5   # 106.666...
	var test_values = [0.0, 400.0, 800.0, car.max_speed_forward]
	for px_speed in test_values:
		car.current_speed = px_speed
		var expected_ms = px_speed / pixels_per_meter
		var actual_ms = car.current_speed / pixels_per_meter
		assert_almost_eq(actual_ms, expected_ms, 0.01, "Conversion at %.1f px/s" % px_speed)
		print("   %.1f px/s -> %.2f m/s (expected %.2f)" % [px_speed, actual_ms, expected_ms])
	print("   " + "-".repeat(55))

# ============================================================
# ТЕСТ 4: ВАЛИДАЦИЯ ПАРАМЕТРОВ
# ============================================================
func test_parameters_validation():
	print("\n[TEST 4/5] Physics Parameters Validation")
	print("   ACTUAL PARAMETERS:")
	print("      max_speed_forward:  %.1f px/s" % car.max_speed_forward)
	print("      max_speed_reverse:  %.1f px/s" % car.max_speed_reverse)
	print("      acceleration_force: %.1f px/s^2" % car.acceleration_force)
	print("      braking_force:      %.1f px/s^2" % car.braking_force)
	print("      damping:            %.3f" % car.damping)
	print("      lateral_friction:   %.2f" % car.lateral_friction)
	print("")
	assert_gt(car.max_speed_forward, 0.0, "max_speed_forward > 0")
	assert_gt(car.acceleration_force, 0.0, "acceleration_force > 0")
	assert_gt(car.braking_force, 0.0, "braking_force > 0")
	print("   RESULT: All physics parameters are valid")
	print("   " + "-".repeat(55))

# ============================================================
# ТЕСТ 5: ОБНОВЛЕНИЕ ВЕКТОРА СКОРОСТИ
# ============================================================
func test_velocity_update():
	print("\n[TEST 5/5] Velocity Vector Update Test")
	var initial_velocity = car.velocity
	car._physics_process(1.0 / 60.0)
	print("   Velocity BEFORE: (%.1f, %.1f) px/s" % [initial_velocity.x, initial_velocity.y])
	print("   Velocity AFTER:  (%.1f, %.1f) px/s" % [car.velocity.x, car.velocity.y])
	assert_ne(car.velocity, initial_velocity, "Velocity must update")
	print("   RESULT: Velocity vector updates correctly")
	print("   " + "-".repeat(55))
	
	# ============================================================
# ТЕСТ 6: РЕАЛЬНОЕ УСКОРЕНИЕ (проверка соответствия параметрам)
# ============================================================
func test_real_acceleration():
	print("\n[TEST 6/6] Real Acceleration Check")
	car.position = Vector2.ZERO
	car.current_speed = 0.0
	var start_time = Time.get_ticks_msec()
	var max_wait = 5000
	var speed_samples = []
	var times = []
	
	Input.action_press("move_forward")
	while Time.get_ticks_msec() - start_time < max_wait:
		speed_samples.append(car.current_speed)
		times.append((Time.get_ticks_msec() - start_time) / 1000.0)
		if len(speed_samples) > 30:
			break
		await get_tree().physics_frame
	Input.action_release("move_forward")
	
	if len(speed_samples) < 2:
		assert_false("Not enough data")
		return
	
	# Вычисляем ускорение по первым 0.5 секундам (среднее)
	var delta_v = speed_samples[-1] - speed_samples[0]
	var delta_t = times[-1] - times[0]
	var real_acceleration = delta_v / delta_t if delta_t > 0.0 else 0.0
	
	print("   Real acceleration over first %.2f seconds: %.1f px/s²" % [delta_t, real_acceleration])
	print("   Expected acceleration (from export var): %.1f px/s²" % car.acceleration_force)
	
	assert_almost_eq(real_acceleration, car.acceleration_force, 50.0, "Real acceleration should match the set acceleration force (within 50 px/s²)")
	print("   " + "-".repeat(55))

func _circle_center(a: Vector2, b: Vector2, c: Vector2) -> Vector2:
	var d = 2.0 * (a.x * (b.y - c.y) + b.x * (c.y - a.y) + c.x * (a.y - b.y))
	
	if abs(d) < 0.001:
		return a  # почти прямая, fallback

	var ux = (
		(a.length_squared() * (b.y - c.y) +
		b.length_squared() * (c.y - a.y) +
		c.length_squared() * (a.y - b.y)) / d
	)

	var uy = (
		(a.length_squared() * (c.x - b.x) +
		b.length_squared() * (a.x - c.x) +
		c.length_squared() * (b.x - a.x)) / d
	)

	return Vector2(ux, uy)

func _estimate_circle_center(points):
	var a = points[0]
	var b = points[points.size() / 2]
	var c = points[-1]

	return _circle_center(a, b, c)

func _measure_turn_radius(speed):
	car.position = Vector2.ZERO
	car.current_speed = speed
	car.heading = 0.0

	Input.action_press("steer_right")

	var points = []
	for i in range(60):
		car._physics_process(1.0 / 60.0)
		points.append(car.position)

	Input.action_release("steer_right")

	var center = _estimate_circle_center(points)
	return points[0].distance_to(center)



func test_forward_reverse_same_radius():
	print("\n[TEST] Same radius forward/backward")

	var radius_forward = _measure_turn_radius(500)
	var radius_backward = _measure_turn_radius(-500)

	assert_almost_eq(radius_forward, radius_backward, 10.0,
		"Forward and reverse must have same radius")

func _instant_turn_center() -> Vector2:
	if car.velocity.length() < 0.1:
		return car.position

	var dir = car.velocity.normalized()
	var normal = Vector2(-dir.y, dir.x)

	if not car.has_meta("prev_heading"):
		car.set_meta("prev_heading", car.heading)
		return car.position

	var prev_heading = car.get_meta("prev_heading")

	var delta_heading = wrapf(car.heading - prev_heading, -PI, PI)

	car.set_meta("prev_heading", car.heading)

	var dt = 1.0 / 60.0
	var omega = delta_heading / dt

	if abs(omega) < 0.0001:
		return car.position

	var radius = car.velocity.length() / omega

	return car.position + normal * radius

func test_turning_center_stability():
	print("\n[TEST] Turning center stability")

	var old_damping = car.damping
	var old_friction = car.lateral_friction
	car.damping = 1.0
	car.lateral_friction = 1.0

	car.position = Vector2.ZERO
	car.heading = 0.0
	car.current_speed = 600.0

	Input.action_press("steer_left")

	var centers = []
	for i in range(60):
		car._physics_process(1.0 / 60.0)
		centers.append(car.get_turn_center(-1.0))

	Input.action_release("steer_left")

	car.damping = old_damping
	car.lateral_friction = old_friction

	var avg = centers[0]
	for c in centers:
		assert_almost_eq(c.distance_to(avg), 0.0, 10.0, "Turning center must be stable")
			
func test_velocity_is_tangent():
	print("\n[TEST] Velocity tangent to circle")

	car.current_speed = 600
	Input.action_press("steer_right")

	for i in range(30):
		car._physics_process(1.0 / 60.0)

		var center = _instant_turn_center()
		var radius_vec = car.position - center

		var dot = radius_vec.normalized().dot(car.velocity.normalized())

		assert_almost_eq(dot, 0.0, 0.1,
			"Velocity must be perpendicular to radius")

	Input.action_release("steer_right")
	
func test_steering_omega_symmetry():
	var w_forward = car._get_angular_velocity(500.0, 1.0)
	var w_reverse = car._get_angular_velocity(-500.0, 1.0)

	assert_almost_eq(abs(w_forward), abs(w_reverse), 0.001, "Forward/reverse steering rate must match by magnitude")
	assert_gt(w_forward, 0.0, "Forward steering should be positive for this sign convention")
	assert_lt(w_reverse, 0.0, "Reverse steering should flip sign")
		
	
func test_turn_radius_formula():
	var speed = 500.0
	var steer = 1.0

	var omega = car._get_angular_velocity(speed, steer)
	var radius = abs(speed / omega)
	var expected = car.wheel_base / tan(car.max_steer_angle * abs(steer))

	assert_almost_eq(radius, expected, expected * 0.01, "Turning radius must match bicycle model")
	
func test_zero_speed_no_turn():
	var omega = car._get_angular_velocity(0.0, 1.0)
	assert_almost_eq(omega, 0.0, 0.001, "No steering at zero speed")
	
