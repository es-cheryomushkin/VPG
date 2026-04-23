extends CharacterBody2D

# ============================================================
# МАСШТАБ И ЕДИНИЦЫ
# ============================================================
const CAR_LENGTH_PX = 480.0
const CAR_LENGTH_M  = 4.5
const PIXELS_PER_METER = CAR_LENGTH_PX / CAR_LENGTH_M

@export var mass: float = 1500.0
@export var is_player := true
@onready var solver = get_node("/root/Node2D/CollisionSolver")
@onready var speed_label: Label = get_node_or_null("/root/Node2D/UI/SpeedLabel")

# ============================================================
# ПАРАМЕТРЫ ДВИЖЕНИЯ
# ============================================================
var max_speed_ms = 15.0

@export var max_speed_forward: float = max_speed_ms * PIXELS_PER_METER
@export var max_speed_reverse: float = 5.0 * PIXELS_PER_METER

var acceleration_ms2 = 3.0
var braking_ms2      = 4.0

@export var acceleration_force: float = acceleration_ms2 * PIXELS_PER_METER
@export var braking_force: float      = braking_ms2 * PIXELS_PER_METER

@export var damping: float = 0.998
@export var lateral_friction: float = 0.1

# Поворот
@export var wheel_base: float = 270.0
@export var max_steer_angle: float = 0.6
@export var min_steering_speed: float = 100.0

# ============================================================
# СОСТОЯНИЕ
# ============================================================
var heading: float = 0.0
var current_speed: float = 0.0

var throttle_input: float = 0.0
var brake_input: bool = false
var steering_input: float = 0.0

var forward_dir: Vector2
var sideways_dir: Vector2

# ============================================================
# ОСНОВНОЙ ЦИКЛ
# ============================================================
var collision_cooldown: float = 0.0
const COLLISION_COOLDOWN_TIME: float = 0.5

func _physics_process(delta: float):
	if collision_cooldown > 0:
		collision_cooldown -= delta
	
	_get_player_input()
	_apply_control(delta)
	_apply_damping(delta)
	_apply_lateral_friction()
	_limit_reverse_speed()
	_update_speedometer()

	var collision = move_and_collide(velocity * delta)
	if collision and collision_cooldown <= 0:
		collision_cooldown = COLLISION_COOLDOWN_TIME
		_handle_collision(collision)

	_update_visual_rotation()

# ============================================================
# УПРАВЛЕНИЕ
# ============================================================
func _get_player_input():
	if not is_player:
		throttle_input = 0.0
		brake_input = false
		steering_input = 0.0
		return

	throttle_input = 1.0 if Input.is_action_pressed("move_forward") else 0.0
	brake_input = Input.is_action_pressed("brake")
	steering_input = Input.get_axis("steer_left", "steer_right")


func _apply_control(delta: float):
	forward_dir = Vector2.RIGHT.rotated(heading)

	if throttle_input > 0.0:
		current_speed += acceleration_force * delta
	if brake_input:
		current_speed -= braking_force * delta

	current_speed = clamp(current_speed, -max_speed_reverse, max_speed_forward)

	var omega = _get_angular_velocity(current_speed, steering_input)
	heading = wrapf(heading + omega * delta, 0.0, TAU)

	forward_dir = Vector2.RIGHT.rotated(heading)
	velocity = forward_dir * current_speed


func _get_angular_velocity(speed: float, steer_input: float) -> float:
	if abs(speed) < min_steering_speed:
		return 0.0

	var steer_angle = steer_input * max_steer_angle
	if abs(steer_angle) < 0.0001:
		return 0.0

	return (speed / wheel_base) * tan(steer_angle)


func get_turn_center(steer_input: float) -> Vector2:
	var steer_angle = steer_input * max_steer_angle

	if abs(current_speed) < min_steering_speed or abs(steer_angle) < 0.0001:
		return position

	var forward = Vector2.RIGHT.rotated(heading)
	var normal = Vector2(-forward.y, forward.x)

	var radius = wheel_base / tan(abs(steer_angle))
	var side = sign(current_speed) * sign(steer_angle)

	return position + normal * side * radius


# ============================================================
# ФИЗИКА
# ============================================================
func _apply_damping(delta: float):
	current_speed *= pow(damping, delta * 60.0)


func _apply_lateral_friction():
	forward_dir = Vector2.RIGHT.rotated(heading)
	sideways_dir = Vector2.UP.rotated(heading)

	var f = velocity.dot(forward_dir)
	var s = velocity.dot(sideways_dir)

	s *= lateral_friction
	velocity = forward_dir * f + sideways_dir * s


func _limit_reverse_speed():
	forward_dir = Vector2.RIGHT.rotated(heading)
	var f = velocity.dot(forward_dir)

	if f < -max_speed_reverse:
		var s = velocity.dot(sideways_dir)
		velocity = forward_dir * (-max_speed_reverse) + sideways_dir * s


func _handle_collision(collision):
	var other = collision.get_collider()
	if not other or not other is CharacterBody2D:
		return
	
	# Проверка на повторное столкновение (по расстоянию)
	if position.distance_to(other.position) < 100.0 and collision_cooldown > 0:
		return
	
	if get_instance_id() > other.get_instance_id():
		return
	
	var normal = collision.get_normal()
	
	# Переводим скорость в м/с
	var v_a_ms = velocity / PIXELS_PER_METER
	var v_b_ms = other.velocity / PIXELS_PER_METER
	
	var body_a_data = {
		"mass": mass,
		"velocity": v_a_ms,
		"rotation": heading
	}
	var body_b_data = {
		"mass": other.mass if "mass" in other else 1500.0,
		"velocity": v_b_ms,
		"rotation": other.rotation
	}
	
	var result = solver.resolve_collision(body_a_data, body_b_data, normal)
	
	if result.size() == 0:
		return
	
	# Применяем новые скорости (переводим обратно в px/s)
	velocity = result.v_a * PIXELS_PER_METER
	other.velocity = result.v_b * PIXELS_PER_METER
	
	# Обновляем current_speed на основе новой скорости
	forward_dir = Vector2.RIGHT.rotated(heading)
	current_speed = velocity.dot(forward_dir)
	
	# Для другой машины тоже обновляем её current_speed, если у неё есть такой параметр
	if other.has_method("_update_internal_speed"):
		other.call("_update_internal_speed")
	
	print("=== COLLISION ===")
	print("Speed before (km/h): %.1f" % (abs(current_speed) / PIXELS_PER_METER * 3.6))
	print("Speed after (km/h): %.1f" % (velocity.length() / PIXELS_PER_METER * 3.6))
	print("Energy (J): %.1f" % result.energy_lost)
	print("Type:", result.type)
	print("Severity:", result.severity)

# ============================================================
# ВИЗУАЛ
# ============================================================
func _update_visual_rotation():
	rotation = heading
	
func _update_internal_speed():
	var forward = Vector2.RIGHT.rotated(heading)
	current_speed = velocity.dot(forward)
	# Дополнительно обновите heading если нужно

func _update_speedometer():
	# Только игрок обновляет UI
	if not is_player:
		return
	
	if not speed_label:
		speed_label = get_tree().root.find_child("SpeedLabel", true, false)
		if not speed_label:
			return
	
	var pixels_per_meter = CAR_LENGTH_PX / CAR_LENGTH_M
	var speed_ms = current_speed / pixels_per_meter
	var speed_kmh = speed_ms * 3.6
	speed_label.text = "Скорость: %d км/ч" % int(speed_kmh)
