extends CharacterBody2D

# Параметры из ТЗ: физическая модель движения 
@export var max_speed = 400.0
@export var steering_speed = 4.0  # Скорость поворота
@export var braking_force = 50.0  # Сила торможения

var current_speed = 0.0

@onready var sensor = $RayCast2D # Ссылка на твой луч

func _physics_process(delta: float) -> void:
	# 1. УПРАВЛЕНИЕ (Ввод данных)
	var turn_input = Input.get_axis("ui_left", "ui_right")
	var speed_input = Input.get_axis("ui_up", "ui_down") # Вперед/назад

	# 2. ПОВОРОТ
	rotation += turn_input * steering_speed * delta

	# 3. ДВИЖЕНИЕ ВПЕРЕД/НАЗАД
	if speed_input < 0: # Нажата стрелка Вверх
		current_speed = move_toward(current_speed, max_speed, 300 * delta)
	elif speed_input > 0: # Нажата стрелка Вниз (Тормоз/Реверс)
		current_speed = move_toward(current_speed, -max_speed / 2, 500 * delta)
	else:
		current_speed = move_toward(current_speed, 0, 100 * delta)

	# Применяем вектор скорости в сторону поворота машины
	velocity = Vector2.from_angle(rotation) * current_speed
	move_and_slide()

	# 4. РАБОТА С СЕНСОРОМ И МЕТРИКАМИ [cite: 47]
	check_safety_metrics(delta)

func check_safety_metrics(delta):
	if sensor.is_colliding():
		var collision_point = sensor.get_collision_point()
		var distance = global_position.distance_to(collision_point)
		
		# Расчет TTC (Time-To-Collision) [cite: 47]
		var ttc = distance / abs(current_speed) if abs(current_speed) > 0.1 else 999.0
		
		# Вывод в консоль для отладки
		print("Дистанция: ", int(distance), " | TTC: ", snapped(ttc, 0.1))
		
		# Реализация предиктивного предотвращения (п. 3.3 ТЗ) [cite: 33, 34]
		#if ttc < 1.0: # Если до удара меньше 1 секунды
			#current_speed = move_toward(current_speed, 0, braking_force * 500 * delta)
			#print("СИСТЕМА АКТИВНОЙ БЕЗОПАСНОСТИ: ТОРМОЖЕНИЕ")
