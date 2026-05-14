extends CharacterBody2D
class_name Car2D

# ============================================================
# Константы
# ============================================================
const PIXELS_PER_METER := 100.0
const COLLISION_COOLDOWN := 0.3
const STATIONARY_CHECK_INTERVAL := 3

# Параметры вращения при столкновении
const MAX_TORQUE_ARM := 225.0
const BASE_MAX_ANG_VEL := 2.0
const FAKE_CONTACT_DISTANCE := 0.3

# Параметры бокового скольжения и вращения
const LATERAL_GRIP := 6.0
const ROTATIONAL_FRICTION := 3.0
const ROTATIONAL_DRAG := 0.1

# ============================================================
# Физические параметры (СИ)
# ============================================================
@export var is_player := true
@export var is_pedestrian := false
@export var ai_controller: AICarController = null
@export var mass_kg := 1500.0
@export var engine_force_N := 4500.0
@export var drag_coefficient := 0.70
@export var rolling_resistance := 30.0
@export var max_steer_angle_rad := 0.6
@export var wheel_base_m := 2.7
@export var brake_force_N := 8000.0

# ============================================================
# Переменные состояния
# ============================================================
var speed_ms := 0.0
var heading_rad := 0.0
var lateral_velocity := Vector2.ZERO
var angular_velocity_ms := 0.0
var moment_of_inertia := 3037.0

# ============================================================
# Управление (входные сигналы)
# ============================================================
var throttle_input := 0.0
var reverse_input := 0.0
var brake_input := 0.0
var steer_input := 0.0

# ============================================================
# Сервисы
# ============================================================
var collision_solver: CollisionSolver = null
var speed_label: Label = null
var _collision_cooldowns: Dictionary = {}
var _stationary_check_counter := 0
var _last_torque_a := 0.0
var _last_torque_b := 0.0


func _ready():
	var root := get_tree().get_root()
	collision_solver = root.find_child("CollisionSolver", true, false)
	speed_label = root.find_child("SpeedLabel", true, false)
	if is_pedestrian:
		_apply_pedestrian_setup()

func _apply_pedestrian_setup():
	var sprite := get_node_or_null("Sprite2D")
	if sprite:
		sprite.region_enabled = false
		sprite.scale = Vector2.ONE
		var path := "res://assets/pedestrians/person.png"
		if FileAccess.file_exists(path):
			sprite.texture = load(path)
	
	var col := get_node_or_null("CollisionShape2D")
	if col:
		col.transform = Transform2D.IDENTITY
		var circle := CircleShape2D.new()
		circle.radius = 100.0
		col.shape = circle
	
	mass_kg = 80.0
	moment_of_inertia = 80.0

# ============================================================
# Основной цикл
# ============================================================
func _physics_process(delta: float):
	_read_input()
	_update_physics(delta)
	_apply_motion(delta)
	rotation = heading_rad
	if is_player:
		_update_speedometer()

func _read_input():
	if is_player:
		throttle_input = 1.0 if Input.is_action_pressed("move_forward") else 0.0
		reverse_input = 1.0 if Input.is_action_pressed("move_backward") else 0.0
		brake_input = 1.0 if Input.is_action_pressed("brake") else 0.0
		steer_input = Input.get_axis("steer_left", "steer_right")
	elif ai_controller != null:
		var ctrl := ai_controller.get_controls()
		throttle_input = ctrl.throttle
		reverse_input = 0.0
		brake_input = ctrl.brake
		steer_input = ctrl.steer
	else:
		throttle_input = 0.0
		reverse_input = 0.0
		brake_input = 0.0
		steer_input = 0.0

func _apply_motion(delta: float):
	var total_velocity := _velocity_vector() + lateral_velocity
	var motion := total_velocity * delta * PIXELS_PER_METER
	
	if motion.length() > 0.1:
		var collision := move_and_collide(motion)
		if collision:
			var other := collision.get_collider() as Car2D
			var v_a := _velocity_vector() + lateral_velocity
			var v_b := other._velocity_vector() + other.lateral_velocity
			_resolve_collision(collision, v_a, v_b, collision.get_position())
	else:
		_stationary_check_counter += 1
		if _stationary_check_counter >= STATIONARY_CHECK_INTERVAL:
			_stationary_check_counter = 0
			_check_while_stationary()

# ============================================================
# Физическая модель
# ============================================================
func _update_physics(delta: float):
	_update_longitudinal(delta)
	_update_steering(delta)
	_update_lateral(delta)
	_update_rotational(delta)
	heading_rad = fmod(heading_rad, TAU)

func _update_longitudinal(delta: float):
	var drive := throttle_input * engine_force_N
	var reverse := -reverse_input * engine_force_N * 0.7
	var brake := 0.0
	if brake_input > 0 and abs(speed_ms) > 0.1:
		brake = -sign(speed_ms) * brake_force_N
	var drag: float = -drag_coefficient * speed_ms * abs(speed_ms)
	var rolling := -rolling_resistance * speed_ms
	
	var accel := (drive + reverse + brake + drag + rolling) / mass_kg
	speed_ms += accel * delta
	speed_ms = clamp(speed_ms, -5.0, 17.0)

func _update_steering(delta: float):
	if abs(speed_ms) <= 0.1:
		return
	var angle := steer_input * max_steer_angle_rad
	if abs(angle) <= 0.001:
		return
	var radius := wheel_base_m / tan(angle)
	heading_rad += speed_ms / radius * delta

func _update_lateral(delta: float):
	if lateral_velocity.length() <= 0.1:
		lateral_velocity = Vector2.ZERO
		return
	var reduction := LATERAL_GRIP * delta
	lateral_velocity = lateral_velocity.normalized() * max(0.0, lateral_velocity.length() - reduction)

func _update_rotational(delta: float):
	if abs(angular_velocity_ms) <= 0.01:
		angular_velocity_ms = 0.0
		return
	angular_velocity_ms -= sign(angular_velocity_ms) * ROTATIONAL_FRICTION * delta
	angular_velocity_ms -= angular_velocity_ms * abs(angular_velocity_ms) * ROTATIONAL_DRAG * delta
	if abs(angular_velocity_ms) < 0.01:
		angular_velocity_ms = 0.0
	heading_rad += angular_velocity_ms * delta

# ============================================================
# Вспомогательные методы
# ============================================================
func _velocity_vector() -> Vector2:
	return Vector2.RIGHT.rotated(heading_rad) * speed_ms

func _forward_dir() -> Vector2:
	return Vector2.RIGHT.rotated(heading_rad)

# ============================================================
# Столкновения — детекция
# ============================================================
func _check_while_stationary():
	if not collision_solver:
		return
	
	var all_cars := get_tree().get_nodes_in_group("cars")
	if all_cars.is_empty():
		var parent := get_parent()
		if parent:
			all_cars = parent.get_children()
	
	for other in all_cars:
		if other == self or not other is Car2D:
			continue
		if position.distance_to(other.position) > 500:
			continue
		
		var normal: Vector2 = (other.position - position).normalized()
		var v_a := _velocity_vector() + lateral_velocity
		var v_b: Vector2 = other._velocity_vector() + other.lateral_velocity
		
		if (v_a - v_b).dot(normal) > -0.1:
			continue
		
		var contact: Vector2 = (position + other.position) / 2.0
		var result := collision_solver.resolve(
			v_a, v_b, mass_kg, other.mass_kg,
			normal, _forward_dir(), other._forward_dir(), contact
		)
		if result.is_empty():
			continue
		
		_apply_collision_result(result, other)
		if get_instance_id() < other.get_instance_id():
			_log_collision(result, v_a, v_b, other)

func _resolve_collision(collision: KinematicCollision2D, v_a: Vector2, v_b: Vector2, contact: Vector2):
	if not collision_solver:
		return
	
	var other := collision.get_collider() as Car2D
	if not other:
		return
	
	var key := "%d_%d" % [mini(get_instance_id(), other.get_instance_id()), maxi(get_instance_id(), other.get_instance_id())]
	var now := Time.get_ticks_msec() / 1000.0
	if _collision_cooldowns.has(key) and now < _collision_cooldowns[key]:
		return
	
	# Определяем, кто обрабатывает столкновение
	var i_move: bool = abs(speed_ms) > 0.01 or lateral_velocity.length() > 0.1
	var other_moves: bool = abs(other.speed_ms) > 0.01 or other.lateral_velocity.length() > 0.1
	if not i_move and other_moves:
		return
	if i_move == other_moves and get_instance_id() > other.get_instance_id():
		return
	
	var result := collision_solver.resolve(
		v_a, v_b, mass_kg, other.mass_kg,
		collision.get_normal(), _forward_dir(), other._forward_dir(), contact
	)
	if result.is_empty():
		return
	
	_apply_collision_result(result, other)
	_collision_cooldowns[key] = now + COLLISION_COOLDOWN
	_log_collision(result, v_a, v_b, other)

# ============================================================
# Столкновения — применение результата
# ============================================================
func _apply_collision_result(result: Dictionary, other: Car2D):
	var fwd := _forward_dir()
	var vel := result.v_a as Vector2
	speed_ms = vel.dot(fwd)
	lateral_velocity = vel - fwd * speed_ms
	
	var other_fwd := other._forward_dir()
	var other_vel := result.v_b as Vector2
	other.speed_ms = other_vel.dot(other_fwd)
	other.lateral_velocity = other_vel - other_fwd * other.speed_ms
	
	_apply_torque(result, other)

func _apply_torque(result: Dictionary, other: Car2D):
	_last_torque_a = 0.0
	_last_torque_b = 0.0
	
	if not result.has("contact_point"):
		return
	
	var contact := result.contact_point as Vector2
	var impulse := result.impulse as Vector2
	var rel_speed := (result.v_a as Vector2 - result.v_b as Vector2).length()
	var speed_factor: float = clamp(rel_speed / 5.0, 0.3, 2.0)
	var max_ang: float = BASE_MAX_ANG_VEL * speed_factor
	
	# Крутящий момент для СЕБЯ
	var r_a := (contact - position).limit_length(MAX_TORQUE_ARM)
	_last_torque_a = r_a.x * impulse.y - r_a.y * impulse.x
	angular_velocity_ms += _last_torque_a / moment_of_inertia
	angular_velocity_ms = clamp(angular_velocity_ms, -max_ang, max_ang)
	
	# Крутящий момент для ДРУГОЙ машины (фейковое плечо)
	var normal := (position - other.position).normalized()
	var fake_contact := other.position + normal * (PIXELS_PER_METER * FAKE_CONTACT_DISTANCE)
	var r_b := (fake_contact - other.position).limit_length(MAX_TORQUE_ARM)
	_last_torque_b = r_b.x * (-impulse).y - r_b.y * (-impulse).x
	other.angular_velocity_ms += _last_torque_b / other.moment_of_inertia
	other.angular_velocity_ms = clamp(other.angular_velocity_ms, -max_ang, max_ang)

# ============================================================
# Логирование и UI
# ============================================================
func _log_collision(result: Dictionary, v_a: Vector2, v_b: Vector2, other: Car2D):
	var who := ""
	if is_player:
		who += "A=player "
	if other.is_player:
		who += "B=player"
	if who != "":
		who = " [" + who.strip_edges() + "]"
	
	print("=== COLLISION%s ===" % who)
	print("  Type: %s | Severity: %s" % [result.type, result.severity])
	print("  Energy lost: %.1f J" % result.energy_lost)
	print("  Car A: pos=(%.0f,%.0f) speed %.1f→%.1f m/s ω %.2f" % [
		position.x, position.y, v_a.length(), speed_ms, angular_velocity_ms
	])
	print("  Car B: pos=(%.0f,%.0f) speed %.1f→%.1f m/s ω %.2f" % [
		other.position.x, other.position.y, v_b.length(), other.speed_ms, other.angular_velocity_ms
	])

func _update_speedometer():
	if speed_label:
		speed_label.text = "%.0f km/h" % (speed_ms * 3.6)
