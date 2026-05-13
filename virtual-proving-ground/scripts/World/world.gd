extends Node2D

## Maximum scenario time in seconds.
## Each scenario will play maximum 10 seconds and then
## switch to next one
const MAX_EPISODE_TIME := 10.0

## Should we play scenarios or show default scene?
##
## Default scene contains ego car (target car that is controlled
## from keyboard) and other car that meves on a track.
## Default track is ellipse-like form.
@export var enable_scenarios := true
@export var cars_container_3d: Node3D
@export var car_3d_scene: PackedScene # Шаблон 3D машинки

## Link to node with name "Cars" on main scene
@onready var _cars_container := $Cars
## Link to scenario label
@onready var _scenario_label := $UI/ScenarioLabel

var scenario_files: PackedStringArray

var current_scenario_index := 0
var current_scenario_entities: Array[Car2D] = []

## current scenario time
var episode_time := 0.0

func _ready():
	$Player/Car.add_to_group("cars")
	
	if not enable_scenarios:
		print("Scenarios disabled (enable_scenarios = false)")
		return
	
	scenario_files = ScenarioLoader.list_scenarios()
	print("Found scenarios: ", scenario_files)
	if scenario_files.size() > 0:
		load_scenario_by_index(current_scenario_index)

func _physics_process(delta: float):
	if not enable_scenarios:
		return
	
	episode_time += delta
	if episode_time >= MAX_EPISODE_TIME:
		_load_next_scenario()
	
	_update_scenario_ui()

func _input(event: InputEvent):
	if not enable_scenarios:
		return
	
	if event.is_action_pressed("next"):
		_load_next_scenario()
	elif event.is_action_pressed("prev"):
		_load_prev_scenario()
	elif event.is_action_pressed("reload"):
		_reload_scenario()

func _load_next_scenario():
	current_scenario_index = wrap(current_scenario_index + 1, 0, scenario_files.size())
	_reload_scenario()

func _load_prev_scenario():
	current_scenario_index = wrap(current_scenario_index - 1, 0, scenario_files.size())
	_reload_scenario()

func _reload_scenario():
	episode_time = 0.0
	load_scenario_by_index(current_scenario_index)

func load_scenario_by_index(index: int):
	_clear_cars() # Это очистит и 2D, и (после нашей правки) 3D
	var player_car := $Player/Car
	var result := ScenarioLoader.load_scenario(scenario_files[index], _cars_container, player_car)
	current_scenario_entities.assign(result.entities)
	
	# --- НОВАЯ ЛОГИКА ДЛЯ 3D ---
	if cars_container_3d:
		for entity in current_scenario_entities:
			if entity is Car2D:
				_create_3d_visual_for(entity)
	# ---------------------------
	
	print("Loaded: \"%s\" — %d cars" % [scenario_files[index], current_scenario_entities.size()])

# Вспомогательная функция для спавна 3D-модели
func _create_3d_visual_for(car_2d: Car2D):
	if not car_3d_scene:
		print("ОШИБКА: Забудь привязать Car3D.tscn в инспекторе узла World!")
		return
		
	var visual = car_3d_scene.instantiate()
	cars_container_3d.add_child(visual)
	
	# Передаем ссылку на 2д оригинал
	visual.target_2d = car_2d
	print("Создана 3D визуализация для: ", car_2d.name)

func _clear_cars():
	for child in _cars_container.get_children():
		child.queue_free()
		
		# Очистка 3D контейнера
	if cars_container_3d:
		for child in cars_container_3d.get_children():
			child.queue_free()
	current_scenario_entities.clear()

func _update_scenario_ui():
	if not _scenario_label or not enable_scenarios:
		return
	var file_name := scenario_files[current_scenario_index] if scenario_files.size() > 0 else "—"
	_scenario_label.text = "Scen: %d/%d\n%s\n %.1f/%.1fs" % [
		current_scenario_index + 1,
		scenario_files.size(),
		file_name,
		episode_time,
		MAX_EPISODE_TIME
	]
