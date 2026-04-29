extends CharacterBody2D
class_name Car2D

# ============================================================
# Константы перевода
# ============================================================
const PIXELS_PER_METER : float = 100

# ============================================================
# Физические параметры (СИ)
# ============================================================
@export var is_player := true
@export var is_pedestrian := false
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
var _collision_cooldowns: Dictionary = {}  # instance_id -> время до следующего столкновения
const COLLISION_COOLDOWN := 0.3  # секунд между столкновениями одной пары

# Счётчик кадров для проверки столкновений стоячей машины
var _stationary_check_counter := 0
const STATIONARY_CHECK_INTERVAL := 3  # проверять каждые 3 кадра

func _ready():
	var root = get_tree().get_root()
	
	var solver_node = root.find_child("CollisionSolver", true, false)
	if solver_node:
		collision_solver = solver_node
	
	var label_node = root.find_child("SpeedLabel", true, false)
	if label_node:
		speed_label = label_node
	
	# Настройки для пешехода
	if is_pedestrian:
		_apply_pedestrian_setup()

func _apply_pedestrian_setup():
	print("Applying pedestrian setup for instance: ", get_instance_id())
	
	# 1. Спрайт: сбрасываем регион и масштаб
	var sprite = get_node_or_null("Sprite2D")
	if sprite:
		sprite.region_enabled = false  # отключаем обрезку 480×192
		sprite.scale = Vector2.ONE     # сбрасываем масштаб
		var path = "res://assets/pedestrians/ped4.png"
		if FileAccess.file_exists(path):
			sprite.texture = load(path)
			print("  Texture loaded, region disabled, scale reset")
		else:
			printerr("  File NOT FOUND: ", path)
	
	# 2. Коллизия: сбрасываем transform и заменяем форму
	var col = get_node_or_null("CollisionShape2D")
	if col:
		col.transform = Transform2D.IDENTITY  # сбрасываем растяжение (scale 21×2)
		var circle = CircleShape2D.new()
		circle.radius = 100.0
		col.shape = circle
		print("  Collision reset: CircleShape2D(radius=25), transform=IDENTITY")
	else:
		printerr("  CollisionShape2D NOT FOUND!")
	
	mass_kg = 80.0
	print("  Pedestrian setup complete")

# ============================================================
# Основной цикл физики
# ============================================================
func _physics_process(delta: float):
	# 1. Считать ввод только для машины игрока
	if is_player:
		throttle_input = 1.0 if Input.is_action_pressed("move_forward") else 0.0
		reverse_input = 1.0 if Input.is_action_pressed("move_backward") else 0.0
		steer_input = Input.get_axis("steer_left", "steer_right")
	
	# 2. Обновить физику
	_update_physics(delta)
	
	# 3. Применить движение ИЛИ проверить столкновения стоя
	var motion_vector = _velocity_vector() * delta * PIXELS_PER_METER
	
	if motion_vector.length() > 0.1:
		# Движемся — обычная обработка
		var collision = move_and_collide(motion_vector)
		if collision:
			_resolve_collision(collision, _velocity_vector(), (collision.get_collider() as Car2D)._velocity_vector())
	else:
		# Стоим — проверяем врезания раз в N кадров
		_stationary_check_counter += 1
		if _stationary_check_counter >= STATIONARY_CHECK_INTERVAL:
			_stationary_check_counter = 0
			_check_while_stationary()
	
	# 4. Визуал и UI
	rotation = heading_rad
	if is_player:
		_update_speedometer()

# ============================================================
# Проверка столкновений для стоячей машины
# ============================================================
func _check_while_stationary():
	if not collision_solver:
		return
	
	# Ищем все машины в дереве
	var all_cars = get_tree().get_nodes_in_group("cars")
	if all_cars.is_empty():
		# Если группы нет, ищем через родителя
		var parent_node = get_parent()
		if parent_node:
			all_cars = parent_node.get_children()
	
	for other in all_cars:
		if other == self or not other is Car2D:
			continue
		
		# Проверяем расстояние между машинами
		var dist = position.distance_to(other.position)
		# Длина машины ~480px, радиус коллизии ~240px
		if dist > 500:
			continue
		
		# Вычисляем нормаль
		var normal = (other.position - position).normalized()
		
		var v_a_old = _velocity_vector()
		var v_b_old = other._velocity_vector()
		
		# Проверяем, движется ли другая машина в нашу сторону
		var rel_vel = v_a_old - v_b_old
		var vel_along_normal = rel_vel.dot(normal)
		
		# Столкновение только если сближаемся
		if vel_along_normal > -0.1:
			continue
		
		var collision_result = collision_solver.resolve(
			v_a_old, v_b_old,
			mass_kg, other.mass_kg,
			normal,
			_forward_dir(), other._forward_dir()
		)
		
		if not collision_result.is_empty():
			# Применяем скорости
			speed_ms = collision_result.v_a.dot(_forward_dir())
			other.speed_ms = collision_result.v_b.dot(other._forward_dir())
			
			# Логирование (только для одной из машин)
			if get_instance_id() < other.get_instance_id():
				_log_collision(collision_result, v_a_old, v_b_old, other)
				
# ============================================================
# Физическая модель (СИ)
# ============================================================
func _update_physics(delta: float):
	var drive_force = throttle_input * engine_force_N
	var reverse_force = -reverse_input * engine_force_N * 0.5
	
	var drag_force = -drag_coefficient * speed_ms * abs(speed_ms)
	var rolling_force = -rolling_resistance * speed_ms
	
	var net_force = drive_force + reverse_force + drag_force + rolling_force
	
	var acceleration = net_force / mass_kg
	speed_ms += acceleration * delta
	
	var max_forward_speed = 16.0
	var max_reverse_speed = 5.0
	speed_ms = clamp(speed_ms, -max_reverse_speed, max_forward_speed)
	
	if abs(speed_ms) > 0.1:
		var steer_angle = steer_input * max_steer_angle_rad
		if abs(steer_angle) > 0.001:
			var turn_radius = wheel_base_m / tan(steer_angle)
			var angular_velocity = speed_ms / turn_radius
			heading_rad += angular_velocity * delta
	
	heading_rad = fmod(heading_rad, TAU)

func _velocity_vector() -> Vector2:
	return Vector2.RIGHT.rotated(heading_rad) * speed_ms

func _forward_dir() -> Vector2:
	return Vector2.RIGHT.rotated(heading_rad)

# ============================================================
# Обработка столкновений (для движущейся машины)
# ============================================================
func _resolve_collision(collision: KinematicCollision2D, v_a_old: Vector2, v_b_old: Vector2):
	if not collision_solver:
		return
	
	var other = collision.get_collider()
	if not other or not other is Car2D:
		return
		
	# В начале _resolve_collision, после получения other:
	var pair_key = str(min(get_instance_id(), other.get_instance_id())) + "_" + str(max(get_instance_id(), other.get_instance_id()))
	var current_time = Time.get_ticks_msec() / 1000.0
	if _collision_cooldowns.has(pair_key) and current_time < _collision_cooldowns[pair_key]:
		return  # кулдаун ещё не прошёл
	
	# Определяем, кто обрабатывает:
	# - Если одна машина движется, а другая нет → движущаяся обрабатывает
	# - Иначе → машина с меньшим instance_id
	var i_am_moving = abs(speed_ms) > 0.01
	var other_is_moving = abs(other.speed_ms) > 0.01
	
	if i_am_moving and not other_is_moving:
		pass  # я обрабатываю
	elif not i_am_moving and other_is_moving:
		return  # обработает другая сторона
	else:
		if get_instance_id() > other.get_instance_id():
			return
	
	var result = collision_solver.resolve(
		v_a_old, v_b_old,
		mass_kg, other.mass_kg,
		collision.get_normal(),
		_forward_dir(), other._forward_dir()
	)
	
	if result.is_empty():
		return
	
	speed_ms = result.v_a.dot(_forward_dir())
	other.speed_ms = result.v_b.dot(other._forward_dir())
	
	_collision_cooldowns[pair_key] = current_time + COLLISION_COOLDOWN
	
	_log_collision(result, v_a_old, v_b_old, other)

# ============================================================
# Логирование столкновений
# ============================================================
func _log_collision(result: Dictionary, v_a_old: Vector2, v_b_old: Vector2, other: Car2D):
	var is_player_a = is_player
	var is_player_b = other.is_player
	var players = []
	if is_player_a: players.append("A=player")
	if is_player_b: players.append("B=player")
	var player_str = ""
	if players.size() > 0: player_str = " [" + ", ".join(players) + "]"
	
	print("=== COLLISION%s ===" % player_str)
	print("  Type: %s | Severity: %s" % [result.type, result.severity])
	print("  Energy lost: %.1f J" % result.energy_lost)
	print("  Car A (id=%d): pos=(%.0f, %.0f), speed %.1f→%.1f m/s (%.0f→%.0f km/h)" % [
		get_instance_id(),
		position.x, position.y,
		v_a_old.length(), speed_ms,
		v_a_old.length() * 3.6, abs(speed_ms) * 3.6
	])
	print("  Car B (id=%d): pos=(%.0f, %.0f), speed %.1f→%.1f m/s (%.0f→%.0f km/h)" % [
		other.get_instance_id(),
		other.position.x, other.position.y,
		v_b_old.length(), other.speed_ms,
		v_b_old.length() * 3.6, abs(other.speed_ms) * 3.6
	])

# ============================================================
# UI
# ============================================================
func _update_speedometer():
	if not speed_label:
		return
	var kmh = abs(speed_ms) * 3.6
	speed_label.text = "%.0f km/h" % kmh
