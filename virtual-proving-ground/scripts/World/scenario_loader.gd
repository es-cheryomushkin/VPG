extends Node

## Loads scenario files from the Python project and spawns cars/pedestrians.
class_name ScenarioLoader

## Path to the Python project scenarios folder, relative to this Godot project
const SCENARIOS_PATH := "../python-virtual-proving-ground/scenarios"
## Preloaded car scene used for instantiating vehicles and pedestrians
const CAR_SCENE = preload("res://scenes/playground/cars.tscn")
## Scale factor: Python uses ~10 px/m, Godot uses ~100 px/m
const PYTHON_TO_GODOT_SCALE: float = 10.0

## Holds all data for a loaded scenario
class Scenario:
	## All cars and pedestrians in this scenario
	var entities: Array = []
	## Scenario display name (from JSON, if present)
	var name: String = ""
	## Scenario description (from JSON, if present)
	var description: String = ""

	func _init(_entities: Array, _name: String, _description: String):
		self.entities = _entities
		self.name = _name
		self.description = _description

	## The first entity in the scenario, typically the player-controlled car
	var ego: Node:
		get:
			if entities.size() > 0:
				return entities[0]
			return null


## Returns a list of .json files found in the scenarios folder.
## Sorted alphabetically by the filesystem.
static func list_scenarios() -> PackedStringArray:
	var dir := DirAccess.open(SCENARIOS_PATH)
	if dir == null:
		push_error("Scenarios directory not found: ", SCENARIOS_PATH)
		return PackedStringArray()

	var result_files := PackedStringArray()
	dir.list_dir_begin()
	var file_name := dir.get_next()
	while file_name != "":
		if file_name.ends_with(".json"):
			result_files.append(file_name)
		file_name = dir.get_next()
	dir.list_dir_end()
	return result_files


## Load a single scenario file and instantiate all its entities.
## [param parent_node] is where new cars/pedestrians will be added (usually $Cars).
## [param existing_ego] if provided, the first car's parameters are applied to it instead of creating a new car.
## Returns a [Scenario] object, or null on failure.
static func load_scenario(file_name: String,
			parent_node: Node, existing_ego: Car2D = null) -> Scenario:
	var file := FileAccess.open(SCENARIOS_PATH + "/" + file_name, FileAccess.READ)
	if file == null:
		push_error("Scenario file not found: ", SCENARIOS_PATH + "/" + file_name)
		return null

	var json := JSON.new()
	if json.parse(file.get_as_text()) != OK:
		push_error("JSON parse error: ", json.get_error_message())
		return null

	var data = json.get_data()
	@warning_ignore("shadowed_variable_base_class")
	var name := ""
	var description := ""
	var entities_data: Array = []

	# JSON can be either a dict with "entities" key or a plain array
	if typeof(data) == TYPE_DICTIONARY:
		name = data.get("name", "")
		description = data.get("description", "")
		entities_data = data.get("entities", [])
	else:
		entities_data = data

	var entities: Array[Car2D] = []
	var first_car := true

	for e_data in entities_data:
		match e_data.get("type", ""):
			"car":
				var car: Car2D
				if first_car and existing_ego:
					# Transfer scenario parameters to the existing player car
					car = existing_ego
					_apply_to(car, e_data)
					car.is_player = true
				else:
					car = _create_car(e_data, parent_node)

				entities.append(car)
				first_car = false

			"pedestrian":
				var ped := _create_pedestrian(e_data, parent_node)
				entities.append(ped)

	return Scenario.new(entities, name, description)


## Create a new car from the preloaded scene and apply scenario data to it
static func _create_car(data: Dictionary, parent: Node) -> Car2D:
	var car := CAR_SCENE.instantiate() as Car2D
	_apply_to(car, data)
	car.is_player = false
	parent.add_child(car)
	car.add_to_group("cars")
	return car


## Apply position, heading, mass, and initial speed from JSON data to a car
static func _apply_to(car: Car2D, data: Dictionary) -> void:
	car.position = Vector2(data.x * PYTHON_TO_GODOT_SCALE, data.y * PYTHON_TO_GODOT_SCALE)
	car.heading_rad = data.get("heading", 0.0)
	car.mass_kg = data.get("mass", 1500.0)
	
	# Compute initial speed: if velocity vector aligns with heading → forward, else → reverse
	var vx: float = data.get("vx", 0.0)
	var vy: float = data.get("vy", 0.0)
	var speed := sqrt(vx * vx + vy * vy)
	var forward := Vector2(cos(car.heading_rad), sin(car.heading_rad))
	car.speed_ms = speed if (vx * forward.x + vy * forward.y) >= 0 else -speed


## Create a pedestrian from the car scene (reuses Car2D with is_pedestrian=true)
static func _create_pedestrian(data: Dictionary, parent: Node) -> Car2D:
	var ped := CAR_SCENE.instantiate() as Car2D
	ped.position = Vector2(data.x * PYTHON_TO_GODOT_SCALE, data.y * PYTHON_TO_GODOT_SCALE)
	ped.is_player = false
	ped.is_pedestrian = true
	ped.mass_kg = data.get("mass", 80.0)
	var vx: float = data.get("vx", 0.0)
	var vy: float = data.get("vy", 0.0)
	ped.speed_ms = sqrt(vx * vx + vy * vy)
	ped.heading_rad = atan2(vy, vx)
	parent.add_child(ped)
	ped.add_to_group("cars")
	return ped
