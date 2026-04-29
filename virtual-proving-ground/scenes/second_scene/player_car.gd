## Скрипт управления автомобилем с видом сверху.
## Отвечает за обработку ввода игрока, физику движения и обновление спидометра в UI.
class_name PlayerCar extends OverheadCarBody2D

## МАСШТАБ СИМУЛЯЦИИ: 1 метр = 100 пикселей.
const PIXELS_PER_METER: float = 100.0
## Коэффициент для перевода скорости из м/с в км/ч.
const MS_TO_KMH: float = 3.6

## Длина машины в метрах.
@export var car_length_m: float = 5.0
## Ширина машины в метрах.
@export var car_width_m: float = 2.0

## Ссылка на UI через абсолютный путь (самый надежный способ).
@onready var speed_label: Label = get_node_or_null("/root/RootNode/LabelCanvasLayer/SpeedLabel")

## Возвращает текущую скорость автомобиля в км/ч.
## Высчитывается динамически на основе встроенного вектора [code]velocity[/code].
var current_speed_kmh: float:
	get:
		return (velocity.length() / PIXELS_PER_METER) * MS_TO_KMH

## Вызывается каждый кадр. В данном случае отвечает только за обновление UI спидометра.
func _process(_delta: float) -> void:
	_update_speedometer_ui()

## Обновляет текстовое поле со скоростью.
## Если нода [Label] не была найдена по абсолютному пути, пытается найти её в дереве сцены.
func _update_speedometer_ui() -> void:
	if speed_label:
		speed_label.text = "Скорость: %d км/ч" % int(current_speed_kmh)
	else:
		# Если не нашел по пути, пробуем найти в дереве (на всякий случай)
		speed_label = get_tree().root.find_child("SpeedLabel", true, false)

## Колбэк управления физикой.
## Считывает оси ввода и передает газ, тормоз и поворот руля в объект [CarInput].
func _provide_input(car_input: CarInput) -> void:
	# Steering: Влево/Вправо
	car_input.steering = Input.get_axis("ui_left", "ui_right")
	# Acceleration: Вперед (ui_up) / Назад (ui_down)
	car_input.acceleration = Input.get_axis("ui_down", "ui_up")
	# Braking: Пробел
	car_input.braking = Input.is_action_pressed("ui_select")
