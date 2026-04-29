extends GutTest

var car : Car2D
var solver : CollisionSolver

func before_each():
	solver = autofree(CollisionSolver.new())
	car = autofree(Car2D.new())
	car.is_player = false
	car.collision_solver = solver
	add_child(car)

func after_each():
	car = null
	solver = null

func test_acceleration_forward():
	car.throttle_input = 1.0
	for i in range(60):
		car._physics_process(1.0/60.0)
	assert_between(car.speed_ms, 2.0, 3.5)
	assert_gt(car.speed_ms, 0.0)

func test_reverse_movement():
	car.reverse_input = 1.0
	for i in range(60):
		car._physics_process(1.0/60.0)
	assert_lt(car.speed_ms, 0.0)
	assert_between(car.speed_ms, -2.0, -0.5)

func test_max_forward_speed_limit():
	car.speed_ms = 50.0
	car._update_physics(1.0/60.0)
	assert_lte(car.speed_ms, 45.0)

func test_max_reverse_speed_limit():
	car.speed_ms = -20.0
	car._update_physics(1.0/60.0)
	assert_gte(car.speed_ms, -15.0)

func test_turning_at_speed():
	car.speed_ms = 10.0
	car.steer_input = 1.0
	var expected_omega = car.speed_ms / (car.wheel_base_m / tan(car.max_steer_angle_rad))
	car._update_physics(1.0/60.0)
	assert_almost_eq(car.heading_rad, expected_omega * 1.0/60.0, 0.01)

func test_no_turning_at_zero_speed():
	car.speed_ms = 0.0
	car.steer_input = 1.0
	car.heading_rad = 0.5
	car._update_physics(1.0/60.0)
	assert_almost_eq(car.heading_rad, 0.5, 0.001)

func test_drag_slows_down():
	car.speed_ms = 30.0
	car.throttle_input = 0.0
	car.reverse_input = 0.0
	var initial = car.speed_ms
	for i in range(30):
		car._physics_process(1.0/60.0)
	assert_lt(car.speed_ms, initial)

func test_velocity_vector_direction():
	car.heading_rad = 0.0
	car.speed_ms = 10.0
	var vel = car._velocity_vector()
	assert_almost_eq(vel.x, 10.0, 0.01)
	assert_almost_eq(vel.y, 0.0, 0.01)

func test_heading_preserved_after_collision():
	var car2 = autofree(Car2D.new())
	car2.is_player = false
	car2.mass_kg = 1500.0
	car2.collision_solver = solver
	add_child(car2)
	
	car.heading_rad = 0.8
	car.speed_ms = 5.0
	car2.heading_rad = 1.2
	car2.speed_ms = 0.0
	
	var old_h1 = car.heading_rad
	var old_h2 = car2.heading_rad
	
	var result = solver.resolve(
		car._velocity_vector(), car2._velocity_vector(),
		car.mass_kg, car2.mass_kg,
		Vector2.LEFT,
		car._forward_dir(), car2._forward_dir()
	)
	
	assert_false(result.is_empty())
	
	car.speed_ms = result.v_a.dot(car._forward_dir())
	car2.speed_ms = result.v_b.dot(car2._forward_dir())
	
	assert_almost_eq(car.heading_rad, old_h1, 0.001)
	assert_almost_eq(car2.heading_rad, old_h2, 0.001)

func test_head_on_collision():
	var car2 = autofree(Car2D.new())
	car2.is_player = false
	car2.mass_kg = 1500.0
	car2.collision_solver = solver
	add_child(car2)
	
	car.heading_rad = 0.0
	car.speed_ms = 10.0
	car2.heading_rad = PI
	car2.speed_ms = 10.0
	
	var result = solver.resolve(
		car._velocity_vector(), car2._velocity_vector(),
		car.mass_kg, car2.mass_kg,
		Vector2.LEFT,
		car._forward_dir(), car2._forward_dir()
	)
	
	assert_false(result.is_empty())
	assert_eq(result.type, "head_on")

func test_collision_with_stationary_different_mass():
	var car2 = autofree(Car2D.new())
	car2.is_player = false
	car2.mass_kg = 3000.0
	car2.collision_solver = solver
	add_child(car2)
	
	car.heading_rad = 0.0
	car.speed_ms = 6.0
	car2.heading_rad = 0.0
	car2.speed_ms = 0.0
	
	var result = solver.resolve(
		car._velocity_vector(), car2._velocity_vector(),
		car.mass_kg, car2.mass_kg,
		Vector2.LEFT,
		car._forward_dir(), car2._forward_dir()
	)
	
	assert_false(result.is_empty())
	
	# При почти неупругом ударе (restitution=0.2) лёгкая машина НЕ отскакивает
	# Она продолжает двигаться вперёд, но медленнее. Тяжёлая начинает двигаться.
	var new_speed_a = result.v_a.dot(car._forward_dir())
	var new_speed_b = result.v_b.dot(car2._forward_dir())
	
	# Обе движутся вперёд после удара
	assert_gt(new_speed_b, 0.0, "Heavy car should move forward")
	assert_gt(new_speed_a, 0.0, "Light car continues forward (inelastic collision)")
	# Но лёгкая замедлилась
	assert_lt(new_speed_a, 6.0, "Light car should slow down")

func test_energy_loss_in_collision():
	var car2 = autofree(Car2D.new())
	car2.is_player = false
	car2.mass_kg = 1500.0
	car2.collision_solver = solver
	add_child(car2)
	
	car.heading_rad = 0.0
	car.speed_ms = 10.0
	car2.heading_rad = 0.0
	car2.speed_ms = 0.0
	
	var result = solver.resolve(
		car._velocity_vector(), car2._velocity_vector(),
		car.mass_kg, car2.mass_kg,
		Vector2.LEFT,
		car._forward_dir(), car2._forward_dir()
	)
	
	assert_false(result.is_empty())
	assert_gt(result.energy_lost, 0.0)
