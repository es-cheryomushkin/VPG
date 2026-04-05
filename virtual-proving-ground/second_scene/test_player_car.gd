extends GutTest

const PlayerCar = preload("res://second_scene/player_car.gd")

var car: PlayerCar
var mock_label: Label

## Вызывается перед каждым тестом. Создаем чистые объекты.
func before_each() -> void:
	# Инициализируем машинку
	car = PlayerCar.new()
	add_child_autofree(car) # GUT автоматически удалит ноду после теста
	
	# фейковый Label для UI, чтобы не зависеть от реальной сцены
	mock_label = Label.new()
	add_child_autofree(mock_label)
	
	# Инжектим Label напрямую
	car.speed_label = mock_label

## Тест 1: Проверка математики расчета скорости в км/ч
func test_current_speed_kmh_calculation() -> void:
	# Проверка состояния покоя
	car.velocity = Vector2.ZERO
	assert_eq(car.current_speed_kmh, 0.0, "При нулевой скорости должно быть 0 км/ч")
	
	# Проверка движения по одной оси (100 пикселей = 1 метр = 3.6 км/ч)
	car.velocity = Vector2(100, 0)
	assert_almost_eq(car.current_speed_kmh, 3.6, 0.01, "Скорость 100 px/s должна равняться 3.6 км/ч")
	
	# Проверка движения по другой оси
	car.velocity = Vector2(0, -500)
	assert_almost_eq(car.current_speed_kmh, 18.0, 0.01, "Скорость 500 px/s должна равняться 18 км/ч")
	
	# Проверка движения по диагонали (вектор 300x400 имеет длину 500)
	car.velocity = Vector2(300, 400)
	assert_almost_eq(car.current_speed_kmh, 18.0, 0.01, "Диагональное движение 300x400 должно давать 18 км/ч")

## Тест 2: Проверка форматирования текста в спидометре
func test_update_speedometer_ui_formatting() -> void:
	# Скорость 3.6 км/ч
	car.velocity = Vector2(100, 0)
	car._update_speedometer_ui()
	# Спецификатор %d должен отбросить дробную часть, не округляя в большую сторону
	assert_eq(mock_label.text, "Скорость: 3 км/ч", "Текст должен корректно форматировать 3.6 как 3")
	
	# Скорость 18 км/ч
	car.velocity = Vector2(500, 0)
	car._update_speedometer_ui()
	assert_eq(mock_label.text, "Скорость: 18 км/ч", "Текст должен корректно обновляться")

## Тест 3: Проверка защиты от падения (null reference)
func test_update_speedometer_ui_no_crash_without_label() -> void:
	# Обнуляем Label, имитируя ситуацию, когда нода не найдена в сцене
	car.speed_label = null
	
	# Вызываем функцию. Если код попытается обратиться к null, тест упадет с ошибкой
	car._update_speedometer_ui()
	
	# Если мы дошли до этой строки, значит функция безопасно обработала отсутствие Label
	assert_true(true, "Функция не должна крашить игру, если Label не найден")

## Тест 4: Проверка маппинга инпутов в объект CarInput
func test_provide_input_default_state() -> void:
	# Создаем инстанс вложенного класса из базового скрипта
	var input_obj = OverheadCarBody2D.CarInput.new()
	
	# Прокидываем его в функцию
	car._provide_input(input_obj)
	
	# Так как мы не симулируем нажатие клавиш в этом тесте,
	# все значения должны считываться как "не нажато"
	assert_eq(input_obj.steering, 0.0, "Руль не должен быть повернут")
	assert_eq(input_obj.acceleration, 0.0, "Педали газа/тормоза не должны быть нажаты")
	assert_false(input_obj.braking, "Ручной тормоз (пробел) не должен быть нажат")
