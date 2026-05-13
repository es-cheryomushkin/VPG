extends "res://addons/gut/test.gd"

var car: Car2D
var test_scene = preload("res://scenes/playground/test_playground.scn")
var world: Node2D
var car_scene = preload("res://scenes/playground/cars.tscn")

func before_all():
	world = test_scene.instantiate()
	get_tree().get_root().add_child(world)
	car = world.get_node("Player/Car")
	await get_tree().create_timer(0.5).timeout

func after_all():
	if world and world.is_inside_tree():
		world.queue_free()

func before_each():
	car.speed_ms = 0.0
	car.heading_rad = 0.0
	car.position = Vector2(200, 400)
	car.throttle_input = 0.0
	car.reverse_input = 0.0
	car.steer_input = 0.0
	Input.action_release("move_forward")
	Input.action_release("move_backward")
	Input.action_release("steer_left")
	Input.action_release("steer_right")
	var cars_node = world.get_node("Cars")
	for child in cars_node.get_children():
		child.queue_free()
	await get_tree().create_timer(0.5).timeout

# ТЕСТ 1: Разгон 0→60 км/ч (6-10 секунд)
func test_realistic_acceleration():
	print("\n[TEST 1] 0→60 km/h Acceleration")
	car.speed_ms = 0.0; car.position = Vector2(100, 400)
	Input.action_press("move_forward")
	var start = Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < 15000:
		await get_tree().physics_frame
		if car.speed_ms >= 16.67:
			var t = (Time.get_ticks_msec() - start) / 1000.0
			print("   ✓ Reached 60 km/h in %.1f s" % t)
			assert_between(t, 6.0, 10.0, "0-60 km/h should take 6-10 seconds")
			break
	Input.action_release("move_forward")
	await get_tree().create_timer(1.0).timeout

# ТЕСТ 2: Тормозной путь с 60 км/ч (10-25 метров)
func test_braking_distance():
	print("\n[TEST 2] Braking Distance from 60 km/h")
	car.speed_ms = 0.0; car.position = Vector2(100, 400); car.heading_rad = 0.0
	Input.action_press("move_forward")
	var start = Time.get_ticks_msec()
	while car.speed_ms < 16.67 and Time.get_ticks_msec() - start < 10000:
		await get_tree().physics_frame
	Input.action_release("move_forward")
	
	var brake_start = car.position.x
	Input.action_press("brake")
	var brake_time = Time.get_ticks_msec()
	while Time.get_ticks_msec() - brake_time < 10000:
		await get_tree().physics_frame
		if car.speed_ms <= 0.5:
			var dist = abs(car.position.x - brake_start) / 100.0
			print("   Braking distance: %.1f m" % dist)
			assert_between(dist, 15.0, 30.0, "Realistic braking distance")
			break
	Input.action_release("brake")
	await get_tree().create_timer(1.0).timeout

# ТЕСТ 3: Максимальная скорость (~60 км/ч)
func test_max_speed():
	print("\n[TEST 3] Maximum Speed Limit")
	car.speed_ms = 0.0; car.position = Vector2(100, 400)
	Input.action_press("move_forward")
	var max_speed = 0.0
	var start = Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < 15000:
		await get_tree().physics_frame
		max_speed = max(max_speed, car.speed_ms)
		if car.speed_ms >= 16.5:
			await get_tree().create_timer(1.0).timeout
			break
	Input.action_release("move_forward")
	print("   Max speed: %.1f m/s (%.0f km/h)" % [max_speed, max_speed * 3.6])
	assert_between(max_speed, 15.0, 18.0, "Max speed should be ~60 km/h")
	await get_tree().create_timer(1.0).timeout

# ТЕСТ 4: Выбег (замедление без газа)
func test_coast_down():
	print("\n[TEST 4] Coast Down from 16 m/s")
	car.speed_ms = 16.0; car.position = Vector2(100, 400)
	car.throttle_input = 0.0; car.reverse_input = 0.0
	var initial = car.speed_ms
	for i in range(180): await get_tree().physics_frame
	var final = car.speed_ms
	var loss = initial - final
	print("   %.1f → %.1f m/s (loss %.1f m/s in 3s)" % [initial, final, loss])
	assert_gt(loss, 0.5, "Should lose speed without throttle")
	await get_tree().create_timer(1.0).timeout

# ТЕСТ 5: Поворот на 90° (велосипедная модель)
func test_turning():
	print("\n[TEST 5] 90° Turn at 10 m/s")
	car.speed_ms = 10.0; car.heading_rad = 0.0; car.position = Vector2(300, 300)
	Input.action_press("steer_right")
	var start = Time.get_ticks_msec()
	var elapsed
	while Time.get_ticks_msec() - start < 5000:
		await get_tree().physics_frame
		if abs(car.heading_rad) >= PI/2:
			elapsed = (Time.get_ticks_msec()-start)/1000.0
			print("   ✓ Turned 90° in %.2f s" % elapsed)
			break
	assert_lt(elapsed, 1.0, "90° turn should take less than 1 second")
	Input.action_release("steer_right")
	await get_tree().create_timer(1.0).timeout

# ТЕСТ 6: Задний ход
func test_reverse():
	print("\n[TEST 6] Reverse Movement")
	car.speed_ms = 3.0; car.position = Vector2(400, 400)
	Input.action_press("move_backward")
	var start = Time.get_ticks_msec()
	var reached = false
	while Time.get_ticks_msec() - start < 8000:
		await get_tree().physics_frame
		if car.speed_ms <= -1.0:
			reached = true
			print("   ✓ Moving backward at %.1f m/s" % car.speed_ms)
			break
	assert_true(reached, "Car should reach -1 m/s in reverse")
	Input.action_release("move_backward")
	await get_tree().create_timer(1.0).timeout

# ТЕСТ 7: Столкновение (сохранение направления)
func test_heading_after_collision():
	print("\n[TEST 7] Heading Preserved After Collision")
	var car2 = car_scene.instantiate()
	world.get_node("Cars").add_child(car2)
	car2.is_player = false; car2.mass_kg = 1500.0
	car2.collision_solver = world.find_child("CollisionSolver", true, false)
	car.heading_rad = 0.0; car.speed_ms = 15.0; car.position = Vector2(200, 400)
	car2.heading_rad = PI; car2.speed_ms = 15.0; car2.position = Vector2(780, 400)
	var h1 = car.heading_rad; var h2 = car2.heading_rad
	Input.action_press("move_forward")
	var start = Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < 5000:
		await get_tree().physics_frame
		if abs(car.speed_ms) < 10.0: break
	Input.action_release("move_forward")
	assert_almost_eq(car.heading_rad, h1, 0.2)
	assert_almost_eq(car2.heading_rad, h2, 0.2)
	await get_tree().create_timer(1.0).timeout

# ТЕСТ 8: Нет поворота на месте
func test_no_steer_at_standstill():
	print("\n[TEST 8] No Steering at Standstill")
	car.speed_ms = 0.0; car.heading_rad = 0.5
	Input.action_press("steer_right")
	for i in range(60): await get_tree().physics_frame
	Input.action_release("steer_right")
	assert_almost_eq(car.heading_rad, 0.5, 0.01)
	await get_tree().create_timer(1.0).timeout

# ТЕСТ 9: Боковое столкновение (проверка боковой скорости)
func test_side_collision():
	print("\n[TEST 9] Side Collision — lateral velocity and rotation")
	var car2 = car_scene.instantiate()
	world.get_node("Cars").add_child(car2)
	car2.is_player = false; car2.mass_kg = 1500.0
	car2.collision_solver = world.find_child("CollisionSolver", true, false)
	
	car.heading_rad = 0.0; car.speed_ms = 0.0; car.position = Vector2(400, 400)
	car2.heading_rad = PI/2; car2.speed_ms = 5.0; car2.position = Vector2(200, -400)
	
	var collision_occurred = false
	var start_time = Time.get_ticks_msec()
	while Time.get_ticks_msec() - start_time < 5000:
		await get_tree().physics_frame
		if not collision_occurred and car.lateral_velocity.length() > 0.1:
			collision_occurred = true
			await get_tree().physics_frame; await get_tree().physics_frame
			break
	
	if collision_occurred:
		print("   Lateral velocity: %.2f m/s, Angular velocity: %.3f rad/s" % [car.lateral_velocity.length(), car.angular_velocity_ms])
		assert_gt(car.lateral_velocity.length(), 0.1, "Car should have lateral velocity after side impact")
		assert_gt(abs(car.angular_velocity_ms), 0.01, "Car should rotate after side impact (got %.3f)" % car.angular_velocity_ms)
		print("   ✓ Side collision physics verified")
	else:
		assert_true(collision_occurred, "Cars should collide")
	
	await get_tree().create_timer(1.0).timeout

# ТЕСТ 10: Столкновение двух движущихся машин
func test_moving_collision():
	print("\n[TEST 10] Moving Collision — both cars in motion")
	
	var car2 = car_scene.instantiate()
	world.get_node("Cars").add_child(car2)
	car2.is_player = false
	car2.mass_kg = 1500.0
	car2.collision_solver = world.find_child("CollisionSolver", true, false)
	
	# Игрок едет вправо
	car.heading_rad = 0.0
	car.speed_ms = 3.0
	car.position = Vector2(200, 400)
	
	# Вторая машина едет вниз, пересечёт траекторию игрока
	car2.heading_rad = PI/2  # вниз
	car2.speed_ms = 10.0
	car2.position = Vector2(800, -800)  # над игроком, но правее
	
	print("   Player: pos=%s, speed=%.1f, heading=%.2f" % [car.position, car.speed_ms, car.heading_rad])
	print("   Car2:   pos=%s, speed=%.1f, heading=%.2f" % [car2.position, car2.speed_ms, car2.heading_rad])
	
	var collision_occurred = false
	var start_time = Time.get_ticks_msec()
	
	while Time.get_ticks_msec() - start_time < 5000:
		await get_tree().physics_frame
		
		# Столкновение = изменилась скорость или появилась боковая
		if not collision_occurred and (abs(car.speed_ms - 3.0) > 0.1 or car.lateral_velocity.length() > 0.1):
			collision_occurred = true
			await get_tree().physics_frame
			await get_tree().physics_frame
			break
	
	if collision_occurred:
		print("   Player speed_ms: %.2f → %.2f m/s" % [3.0, car.speed_ms])
		print("   Player lateral_velocity: (%.2f, %.2f) length=%.2f m/s" % [car.lateral_velocity.x, car.lateral_velocity.y, car.lateral_velocity.length()])
		print("   Player angular_velocity: %.3f rad/s" % car.angular_velocity_ms)
		
		assert_true(abs(car.speed_ms - 3.0) > 0.1 or car.lateral_velocity.length() > 0.1,
			"Car should change velocity after collision")
		print("   ✓ Moving collision detected")
	else:
		print("   ⚠ No collision detected")
		print("   Final: Player=%s, Car2=%s" % [car.position, car2.position])
		assert_true(collision_occurred, "Moving cars should collide")
	
	await get_tree().create_timer(1.0).timeout
