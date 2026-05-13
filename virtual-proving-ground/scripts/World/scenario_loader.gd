extends Node
class_name ScenarioLoader

# Путь к папке со сценариями
const SCENARIOS_PATH = "E:/VPG/python-virtual-proving-ground/scenarios"
const car_scene = preload("res://scenes/playground/cars.tscn")

# Коэффициент пересчёта координат из Python-проекта в Godot
const PYTHON_TO_GODOT_SCALE: float = 10

## Загружает сценарий по имени файла и создаёт машины в parent_node.
## Если передан existing_ego, первая машина в сценарии не создаётся,
## а её параметры передаются в existing_ego.
## Возвращает словарь с ключами: entities (Array[Car2D]), name, description, ego (Car2D или null).
static func load_scenario(file_name: String, parent_node: Node, existing_ego: Car2D = null) -> Dictionary:
	var file_path = SCENARIOS_PATH + "/" + file_name
	var file = FileAccess.open(file_path, FileAccess.READ)
	if file == null:
		printerr("Failed to open scenario file: ", file_path)
		return {"entities": [], "name": "", "description": "", "ego": null}

	var json_text = file.get_as_text()
	file.close()

	var json = JSON.new()
	var error = json.parse(json_text)
	if error != OK:
		printerr("Failed to parse JSON: ", json.get_error_message())
		return {"entities": [], "name": "", "description": "", "ego": null}

	var data = json.get_data()

	@warning_ignore("shadowed_variable_base_class")
	var name = ""
	var description = ""
	var entities_data = []

	if typeof(data) == TYPE_DICTIONARY:
		name = data.get("name", "")
		description = data.get("description", "")
		entities_data = data.get("entities", [])
	else:
		entities_data = data

	var entities = []
	var ego_car = null
	var first_car = true

	for e_data in entities_data:
		if e_data.get("type") == "car":
			var pos_x = e_data.get("x", 0) * PYTHON_TO_GODOT_SCALE
			var pos_y = e_data.get("y", 0) * PYTHON_TO_GODOT_SCALE
			var heading = e_data.get("heading", 0)
			var mass = e_data.get("mass", 1500)
			
			# Начальная скорость из vx, vy (м/с)
			var vx = e_data.get("vx", 0.0)
			var vy = e_data.get("vy", 0.0)
			var speed = sqrt(vx * vx + vy * vy)
			var forward = Vector2(cos(heading), sin(heading))
			var dot = vx * forward.x + vy * forward.y
			var initial_speed = speed if dot >= 0 else -speed
			
			var car: Car2D
			
			if first_car and existing_ego != null:
				car = existing_ego
				car.position = Vector2(pos_x, pos_y)
				car.heading_rad = heading
				car.mass_kg = mass
				car.speed_ms = initial_speed
				car.is_player = true
			else:
				car = car_scene.instantiate()
				car.position = Vector2(pos_x, pos_y)
				car.heading_rad = heading
				car.mass_kg = mass
				car.is_player = false
				car.speed_ms = initial_speed
				parent_node.add_child(car)
				car.add_to_group("cars")
			
			entities.append(car)
			if ego_car == null:
				ego_car = car
			
			first_car = false

		elif e_data.get("type") == "pedestrian":
			var vx = e_data.get("vx", 0.0)
			var vy = e_data.get("vy", 0.0)
			var pedestrian = car_scene.instantiate()
			pedestrian.position = Vector2(
				e_data.get("x", 0) * PYTHON_TO_GODOT_SCALE,
				e_data.get("y", 0) * PYTHON_TO_GODOT_SCALE
			)
			pedestrian.is_player = false
			pedestrian.is_pedestrian = true
			pedestrian.mass_kg = e_data.get("mass", 80)
			pedestrian.speed_ms = sqrt(vx*vx + vy*vy)  # скорость без знака
			pedestrian.heading_rad = atan2(vy, vx)
			parent_node.add_child(pedestrian)
			pedestrian.add_to_group("cars")

	return {"entities": entities, "name": name, "description": description, "ego": ego_car}

## Возвращает список .json файлов в папке сценариев
static func list_scenarios() -> PackedStringArray:
	var files = PackedStringArray()
	var dir = DirAccess.open(SCENARIOS_PATH)
	if dir == null:
		printerr("Failed to open scenarios directory: ", SCENARIOS_PATH)
		return files

	dir.list_dir_begin()
	var file_name = dir.get_next()
	while file_name != "":
		if file_name.ends_with(".json"):
			files.append(file_name)
		file_name = dir.get_next()
	dir.list_dir_end()
	return files
