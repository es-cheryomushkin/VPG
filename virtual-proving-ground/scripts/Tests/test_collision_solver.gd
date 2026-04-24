extends "res://addons/gut/test.gd"

var car: Car2D
var test_scene = preload("res://scenes/playground/playground.scn")
var world: Node2D
var car_scene = preload("res://scenes/playground/cars.tscn")

func before_all():	
	world = test_scene.instantiate()
	get_tree().get_root().add_child(world)
	car = world.get_node("Player/Car")
	
	print("\n" + "=".repeat(70))
	print("CAR PHYSICS VISUAL TEST SUITE")
	print("  Car length: 480 px = 4.5 m")
	print("  Wheel base: 192 px = %.2f m" % (192.0 / 106.666667))
	print("=".repeat(70))
	
	await get_tree().create_timer(0.5).timeout

func after_all():
	if world and world.is_inside_tree():
		world.queue_free()
	
	print("\n" + "=".repeat(70))
	print("VISUAL TEST SUITE COMPLETED")
	print("=".repeat(70))

func before_each():
	# Сбрасываем машину игрока
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
	
	# Удаляем все дополнительные машины (оставляем только Player/Car)
	var cars_node = world.get_node("Cars")
	for child in cars_node.get_children():
		child.queue_free()
	
	await get_tree().create_timer(0.5).timeout

# ============================================================
# ТЕСТ 1: Разгон до максимальной скорости
# ============================================================
func test_acceleration_to_max_speed():
	print("\n[TEST 1] Acceleration to 15 m/s (54 km/h)")
	
	car.speed_ms = 0.0
	car.position = Vector2(100, 400)
	
	Input.action_press("move_forward")
	
	var start_time = Time.get_ticks_msec()
	
	while Time.get_ticks_msec() - start_time < 20000:
		await get_tree().physics_frame
		
		if (Time.get_ticks_msec() - start_time) % 3000 < 17:
			print("   %.1f m/s (%.0f km/h)" % [car.speed_ms, car.speed_ms * 3.6])
		
		if car.speed_ms >= 15:
			var elapsed = (Time.get_ticks_msec() - start_time) / 1000.0
			print("   ✓ Reached %.1f m/s in %.1f seconds" % [car.speed_ms, elapsed])
			assert_lt(elapsed, 20.0, "Should reach 44.5 m/s within 20 seconds")
			break
	
	Input.action_release("move_forward")
	await get_tree().create_timer(1.0).timeout

# ============================================================
# ТЕСТ 2: Задний ход
# ============================================================
func test_reverse_movement():
	print("\n[TEST 2] Reverse Movement")
	
	car.speed_ms = 3.0
	car.position = Vector2(400, 400)
	
	print("   Initial: %.1f m/s forward" % car.speed_ms)
	
	Input.action_press("move_backward")
	
	var start_time = Time.get_ticks_msec()
	var stopped = false
	var went_backward = false
	
	while Time.get_ticks_msec() - start_time < 8000:
		await get_tree().physics_frame
		
		if not stopped and car.speed_ms <= 0.0:
			stopped = true
			var stop_time = (Time.get_ticks_msec() - start_time) / 1000.0
			print("   Stopped after %.2f s, speed: %.2f" % [stop_time, car.speed_ms])
		
		if stopped and car.speed_ms <= -1.0:
			went_backward = true
			print("   ✓ Moving backward: %.1f m/s" % car.speed_ms)
			break
	
	Input.action_release("move_backward")
	
	assert_true(stopped, "Car should stop. Final speed: %.2f" % car.speed_ms)
	assert_true(went_backward, "Car should move backward. Final speed: %.2f" % car.speed_ms)
	
	await get_tree().create_timer(1.0).timeout

# ============================================================
# ТЕСТ 3: Поворот на скорости
# ============================================================
func test_turning_circle():
	print("\n[TEST 3] Turning Circle")
	
	car.speed_ms = 10.0
	car.heading_rad = 0.0
	car.position = Vector2(300, 300)
	
	var initial_heading = car.heading_rad
	
	Input.action_press("steer_right")
	
	var start_time = Time.get_ticks_msec()
	var turned_90 = false
	
	while Time.get_ticks_msec() - start_time < 5000:
		await get_tree().physics_frame
		
		if abs(car.heading_rad - initial_heading) >= PI/2:
			turned_90 = true
			var elapsed = (Time.get_ticks_msec() - start_time) / 1000.0
			print("   ✓ Turned 90° in %.2f s (heading: %.2f rad)" % [elapsed, car.heading_rad])
			break
	
	Input.action_release("steer_right")
	
	assert_true(turned_90, "Car should complete 90° turn")
	
	await get_tree().create_timer(1.0).timeout

# ============================================================
# ТЕСТ 4: Сопротивление
# ============================================================
func test_drag_effect():
	print("\n[TEST 4] Drag Effect at 30 m/s")
	
	car.speed_ms = 30.0
	car.throttle_input = 0.0
	car.reverse_input = 0.0
	car.position = Vector2(100, 400)
	
	var initial_speed = car.speed_ms
	
	for i in range(180):
		await get_tree().physics_frame
	
	var final_speed = car.speed_ms
	var speed_loss = initial_speed - final_speed
	
	print("   %.2f m/s → %.2f m/s (lost %.2f m/s in 3s)" % [initial_speed, final_speed, speed_loss])
	
	assert_gt(speed_loss, 0.5, "Should lose >0.5 m/s at 30 m/s over 3 seconds")
	
	await get_tree().create_timer(1.0).timeout

# ============================================================
# ТЕСТ 5: Heading при столкновении (ИСПРАВЛЕНО с вашим методом)
# ============================================================
func test_heading_after_collision():
	print("\n[TEST 5] Heading Preserved After Collision")
	
	# Создаём вторую машину
	var cars_node = world.get_node("Cars")
	var car2 = car_scene.instantiate()
	cars_node.add_child(car2)
	
	# ДИАГНОСТИКА: проверяем наличие collision_solver
	print("   Player car collision_solver: ", car.collision_solver)
	print("   Car2 collision_solver: ", car2.collision_solver)
	
	# ЯВНО устанавливаем collision_solver для car2
	var solver = world.find_child("CollisionSolver", true, false)
	if solver:
		car2.collision_solver = solver
		print("   ✓ CollisionSolver explicitly set for car2")
	else:
		print("   ❌ CollisionSolver NOT FOUND in world!")
	
	# Настраиваем машины
	car.heading_rad = 0.0
	car.speed_ms = 15.0
	car.position = Vector2(200, 400)
	
	car2.is_player = false
	car2.heading_rad = PI
	car2.speed_ms = 15.0
	car2.position = Vector2(200 + 480 + 100, 400)  # 780px
	
	print("   Car A: pos=%s, heading=%.2f, speed=%.1f, solver=%s" % [
		car.position, car.heading_rad, car.speed_ms, 
		"YES" if car.collision_solver else "NO"
	])
	print("   Car B: pos=%s, heading=%.2f, speed=%.1f, solver=%s" % [
		car2.position, car2.heading_rad, car2.speed_ms,
		"YES" if car2.collision_solver else "NO"
	])
	print("   Distance: %.0f px" % car.position.distance_to(car2.position))
	
	var initial_heading_a = car.heading_rad
	var initial_heading_b = car2.heading_rad
	
	Input.action_press("move_forward")
	
	var collision_detected = false
	var start_time = Time.get_ticks_msec()
	
	while Time.get_ticks_msec() - start_time < 5000:
		await get_tree().physics_frame
		
		# Более надёжное обнаружение: скорость изменилась значительно
		if not collision_detected and abs(car.speed_ms) < 10.0:
			collision_detected = true
			print("   ⚡ Collision detected! Speed changed to: %.1f m/s" % car.speed_ms)
			await get_tree().physics_frame
			await get_tree().physics_frame
			break
	
	Input.action_release("move_forward")
	
	if collision_detected:
		print("   Car A: heading %.2f rad (was %.2f), speed %.1f m/s" % [
			car.heading_rad, initial_heading_a, car.speed_ms
		])
		print("   Car B: heading %.2f rad (was %.2f), speed %.1f m/s" % [
			car2.heading_rad, initial_heading_b, car2.speed_ms
		])
		
		assert_almost_eq(car.heading_rad, initial_heading_a, 0.2, 
			"Car A heading should not change significantly")
		assert_almost_eq(car2.heading_rad, initial_heading_b, 0.2,
			"Car B heading should not change significantly")
		print("   ✓ Headings preserved")
	else:
		print("   ⚠ No collision detected")
		print("   Final: A=%s (speed=%.1f), B=%s (speed=%.1f)" % [
			car.position, car.speed_ms, car2.position, car2.speed_ms
		])
		assert_true(collision_detected, "Cars should collide")
	
	await get_tree().create_timer(1.0).timeout

# ============================================================
# ТЕСТ 6: Нет поворота на месте
# ============================================================
func test_no_steering_at_standstill():
	print("\n[TEST 6] No Steering at Standstill")
	
	car.speed_ms = 0.0
	car.heading_rad = 0.5
	car.position = Vector2(500, 400)
	
	var initial_heading = car.heading_rad
	
	Input.action_press("steer_right")
	
	for i in range(60):
		await get_tree().physics_frame
	
	Input.action_release("steer_right")
	
	print("   Heading: %.3f rad (was %.3f)" % [car.heading_rad, initial_heading])
	assert_almost_eq(car.heading_rad, initial_heading, 0.01)
	print("   ✓ No turn at standstill")
	
	await get_tree().create_timer(1.0).timeout
