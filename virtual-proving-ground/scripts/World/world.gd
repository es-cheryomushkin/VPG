extends Node2D

## Maximum scenario time in seconds.
## Each scenario will play maximum 10 seconds and then
## switch to next one
const MAX_EPISODE_TIME := 10.0

## Should we play scenarios or show default scene?
##
## Default scene contains ego car (target car that is controlled
## from keyboard) and other car that moves on a track.
## Default track is ellipse-like form.
@export var enable_scenarios := true

## Link to node with name "Cars" on main scene
@onready var _cars_container := $Cars
## Link to scenario label
@onready var _scenario_label := $UI/ScenarioLabel

## List of .json scenario files found in the scenarios folder
var scenario_files: PackedStringArray

## Index of the currently playing scenario
var current_scenario_index := 0
## Cars and pedestrians currently on the scene
var current_scenario_entities: Array[Car2D] = []

## Elapsed time since current scenario started (seconds)
var episode_time := 0.0


func _ready():
	# Add player car to "cars" group so it can be found by collision checks
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
	# Auto-advance to next scenario when time runs out
	if episode_time >= MAX_EPISODE_TIME:
		_load_next_scenario()
	
	_update_scenario_ui()


func _input(event: InputEvent):
	if not enable_scenarios:
		return
	
	# Manual scenario switching
	if event.is_action_pressed("next"):
		_load_next_scenario()
	elif event.is_action_pressed("prev"):
		_load_prev_scenario()
	elif event.is_action_pressed("reload"):
		_reload_scenario()


## Advance to the next scenario, wrapping around to the first
func _load_next_scenario():
	current_scenario_index = wrap(current_scenario_index + 1, 0, scenario_files.size())
	_reload_scenario()


## Go back to the previous scenario, wrapping around to the last
func _load_prev_scenario():
	current_scenario_index = wrap(current_scenario_index - 1, 0, scenario_files.size())
	_reload_scenario()


## Restart the current scenario from the beginning
func _reload_scenario():
	episode_time = 0.0
	load_scenario_by_index(current_scenario_index)


## Load a scenario file by its index in scenario_files.
## Clears existing cars, creates new ones, and assigns the player car as ego.
func load_scenario_by_index(index: int):
	_clear_cars()
	var player_car := $Player/Car
	var result := ScenarioLoader.load_scenario(scenario_files[index], _cars_container, player_car)
	current_scenario_entities.assign(result.entities)
	print("Loaded: \"%s\" — %d cars" % [scenario_files[index], current_scenario_entities.size()])


## Remove all scenario-spawned cars from the scene
func _clear_cars():
	for child in _cars_container.get_children():
		child.queue_free()
	current_scenario_entities.clear()


## Update the scenario info label (name, progress, number)
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
