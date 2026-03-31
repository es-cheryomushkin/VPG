extends OverheadCarBody2D

## МАСШТАБ СИМУЛЯЦИИ: 1 метр = 100 пикселей.
const PIXELS_PER_METER = 100.0
const MS_TO_KMH = 3.6

@export var car_length_m: float = 5.0
@export var car_width_m: float = 2.0

## Ссылка на UI через абсолютный путь (самый надежный способ).
@onready var speed_label: Label = get_node_or_null("/root/Node2D/CanvasLayer/SpeedLabel")

## Геттер скорости в км/ч.
var current_speed_kmh: float:
	get:
		# velocity — встроенная переменная
		return (velocity.length() / PIXELS_PER_METER) * MS_TO_KMH

func _process(_delta: float) -> void:
	_update_speedometer_ui()

func _update_speedometer_ui() -> void:
	if speed_label:
		speed_label.text = "Скорость: %d км/ч" % int(current_speed_kmh)
	else:
		# Если не нашел по пути, пробуем найти в дереве (на всякий случай)
		speed_label = get_tree().root.find_child("SpeedLabel", true, false)

## Колбэк управления физикой.
func _provide_input(car_input: CarInput) -> void:
	# Steering: Влево/Вправо
	car_input.steering = Input.get_axis("ui_left", "ui_right")
	# Acceleration: Вперед (ui_up) / Назад (ui_down)
	car_input.acceleration = Input.get_axis("ui_down", "ui_up")
	# Braking: Пробел
	car_input.braking = Input.is_action_pressed("ui_select")
