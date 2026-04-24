extends CharacterBody2D
class_name Car2D

# ============================================================
# Константы перевода
# ============================================================
const PIXELS_PER_METER : float = 106.67   # 480px / 4.5m

# ============================================================
# Физические параметры (СИ)
# ============================================================
@export var is_player := true
@export var mass_kg : float = 1500.0
@export var engine_force_N : float = 4500.0
@export var drag_coefficient : float = 0.35
@export var rolling_resistance : float = 12.0
@export var max_steer_angle_rad : float = 0.6
@export var wheel_base_m : float = 2.7

# ============================================================
# Переменные состояния
# ============================================================
var speed_ms : float = 0.0           # продольная скорость (положительная = вперёд)
var heading_rad : float = 0.0        # угол направления машины (куда смотрит капот)

# ============================================================
# Управление (входные сигналы)
# ============================================================
var throttle_input : float = 0.0     # 0..1 (вперёд)
var reverse_input : float = 0.0      # 0..1 (назад)
var steer_input : float = 0.0        # -1..1 (поворот)

# ============================================================
# Сервисы
# ============================================================
var collision_solver = null
var speed_label : Label = null

func _ready():
	# Ищем от самого верха дерева сцены
	var root = get_tree().get_root()
	
	var solver_node = root.find_child("CollisionSolver", true, false)
	if solver_node:
		collision_solver = solver_node
	
	var label_node = root.find_child("SpeedLabel", true, false)
	if label_node:
		speed_label = label_node

# ============================================================
# Основной цикл физики
# ============================================================
func _physics_process(delta: float):
	# 1. Считать ввод только для машины игрока
	if is_player:
		# Вперёд: W
		throttle_input = 1.0 if Input.is_action_pressed("move_forward") else 0.0
		# Назад: S
		reverse_input = 1.0 if Input.is_action_pressed("move_backward") else 0.0
		# Поворот: A/D
		steer_input = Input.get_axis("steer_left", "steer_right")
	
	# 2. Обновить физику
	_update_physics(delta)
	
	# 3. Применить движение
	var motion_vector = _velocity_vector() * delta * PIXELS_PER_METER
	var collision = move_and_collide(motion_vector)
	if collision:
		_resolve_collision(collision)
	
	# 4. Визуал и UI
	rotation = heading_rad
	if is_player:
		_update_speedometer()

# ============================================================
# Физическая модель (СИ)
# ============================================================
func _update_physics(delta: float):
	# Сила тяги вперёд
	var drive_force = throttle_input * engine_force_N
	
	# Сила тяги назад
	var reverse_force = -reverse_input * engine_force_N * 0.5  # задний ход слабее
	
	# Силы сопротивления (всегда против движения)
	var drag_force = -drag_coefficient * speed_ms * abs(speed_ms)
	var rolling_force = -rolling_resistance * speed_ms
	
	var net_force = drive_force + reverse_force  + drag_force + rolling_force
	
	# Второй закон Ньютона
	var acceleration = net_force / mass_kg
	speed_ms += acceleration * delta
	
	# Ограничение скорости
	var max_forward_speed = 16.0   # м/с (~60 км/ч)
	var max_reverse_speed = 5.0    # м/с (~18 км/ч)
	speed_ms = clamp(speed_ms, -max_reverse_speed, max_forward_speed)
	
	# Поворот (велосипедная модель)
	if abs(speed_ms) > 0.1:
		var steer_angle = steer_input * max_steer_angle_rad
		if abs(steer_angle) > 0.001:
			var turn_radius = wheel_base_m / tan(steer_angle)
			var angular_velocity = speed_ms / turn_radius
			heading_rad += angular_velocity * delta
	
	heading_rad = fmod(heading_rad, TAU)

func _velocity_vector() -> Vector2:
	# Скорость всегда направлена туда, куда смотрит машина
	# Положительная speed_ms = вперёд, отрицательная = назад
	return Vector2.RIGHT.rotated(heading_rad) * speed_ms

func _forward_dir() -> Vector2:
	return Vector2.RIGHT.rotated(heading_rad)

# ============================================================
# Обработка столкновений
# ============================================================
func _resolve_collision(collision: KinematicCollision2D):
	if not collision_solver:
		return
	
	var other = collision.get_collider()
	if not other or not other is Car2D:
		return
	
	# Вычисляем результат столкновения
	var result = collision_solver.resolve(
		_velocity_vector(), other._velocity_vector(),
		mass_kg, other.mass_kg,
		collision.get_normal(),
		_forward_dir(), other._forward_dir()
	)
	
	if result.is_empty():
		return
	
	# Применяем новые скорости
	# ВАЖНО: не меняем heading_rad! Только продольную скорость и направление движения
	var new_velocity_a = result.v_a   # полный вектор скорости в м/с
	var new_velocity_b = result.v_b
	
	# Проецируем новую скорость на направление машины (сохраняем heading_rad!)
	var forward_a = _forward_dir()
	var forward_b = other._forward_dir()
	
	# Продольная скорость = проекция на forward_dir
	speed_ms = new_velocity_a.dot(forward_a)

	# Применяем к другой машине
	other.speed_ms = new_velocity_b.dot(forward_b)
	
	# Логирование (только для одной из машин)
	if get_instance_id() < other.get_instance_id():
		print("Collision: Type=%s, Energy lost=%.1f J" % [result.type, result.energy_lost])
		print("  Car A speed: %.1f km/h → %.1f km/h" % [
			(result.v_a - result.impulse / mass_kg).length() * sign(speed_ms) * 3.6, 
			speed_ms * 3.6
		])

# ============================================================
# UI
# ============================================================
func _update_speedometer():
	if not speed_label:
		return
	var kmh = abs(speed_ms) * 3.6
	speed_label.text = "%.0f km/h" % kmh
