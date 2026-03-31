extends CharacterBody2D

# Параметры из ТЗ: физическая модель движения 
@export var max_speed = 400.0
@export var steering_speed = 4.0  # Скорость поворота
@export var braking_force = 10.0  # Сила торможения

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
