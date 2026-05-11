extends Node2D

@export var enable_scenarios := true

@onready var _cars_container := $Cars
@onready var _scenario_label := $UI/ScenarioLabel

var current_scenario_index := 0
var scenario_files: PackedStringArray
var scenario_entities: Array[Car2D] = []

var episode_time := 0.0
const MAX_EPISODE_TIME := 10.0

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
	_clear_cars()
	var player_car := $Player/Car
	var result := ScenarioLoader.load_scenario(scenario_files[index], _cars_container, player_car)
	scenario_entities.assign(result.entities)
	print("Loaded: \"%s\" — %d cars" % [scenario_files[index], scenario_entities.size()])

func _clear_cars():
	for child in _cars_container.get_children():
		child.queue_free()
	scenario_entities.clear()

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
