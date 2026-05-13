extends Node2D

@export var enable_scenarios := true  # Переключатель в инспекторе

@onready var cars = $Cars
@onready var scenario_label = $UI/ScenarioLabel
var car_scene = preload("res://scenes/playground/cars.tscn")
#var scenario_scene = preload("res://scenes/playground/scenario_playground.scn")
var world: Node2D
	
var current_scenario_index := 0
var scenario_files: PackedStringArray
var scenario_entities: Array = []

var episode_time := 0.0
const MAX_EPISODE_TIME := 10.0

func _ready():
	$Player/Car.add_to_group("cars")
	
	if enable_scenarios:
		#world = scenario_scene.instantiate()
		scenario_files = ScenarioLoader.list_scenarios()
		print("Found scenarios: ", scenario_files)
		if scenario_files.size() > 0:
			load_scenario_by_index(current_scenario_index)
	else:
		print("Scenarios disabled (enable_scenarios = false)")

func _physics_process(delta):
	if not enable_scenarios:
		return
	
	episode_time += delta
	if episode_time >= MAX_EPISODE_TIME:
		next_scenario()
	
	_update_scenario_ui()

func _input(event):
	if not enable_scenarios:
		return
	
	if event.is_action_pressed("next"):
		next_scenario()
	elif event.is_action_pressed("prev"):
		prev_scenario()
	elif event.is_action_pressed("reload"):
		reload_scenario()

func next_scenario():
	current_scenario_index = (current_scenario_index + 1) % scenario_files.size()
	reload_scenario()

func prev_scenario():
	current_scenario_index = current_scenario_index - 1
	if current_scenario_index < 0:
		current_scenario_index = scenario_files.size() - 1
	reload_scenario()

func reload_scenario():
	episode_time = 0.0
	load_scenario_by_index(current_scenario_index)

func load_scenario_by_index(index: int):
	_clear_all_cars()
	var file_name = scenario_files[index]
	var player_car = $Player/Car
	var result = ScenarioLoader.load_scenario(file_name, $Cars, player_car)
	scenario_entities = result.entities
	print("Loaded: \"%s\" — %d cars" % [file_name, scenario_entities.size()])

func _clear_all_cars():
	for child in $Cars.get_children():
		child.queue_free()
	scenario_entities.clear()

func _update_scenario_ui():
	if not scenario_label or not enable_scenarios:
		return
	var file_name = scenario_files[current_scenario_index] if scenario_files.size() > 0 else "—"
	var text = "Scen: %d/%d\n%s\n %.1f/%.1fs" % [
		current_scenario_index + 1,
		scenario_files.size(),
		file_name,
		episode_time,
		MAX_EPISODE_TIME
	]
	scenario_label.text = text
