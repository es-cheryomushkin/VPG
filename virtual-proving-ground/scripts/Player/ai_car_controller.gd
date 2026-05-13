extends Node
class_name AICarController

@export var waypoints: Array[Vector2] = []
@export var waypoint_radius := 120.0
@export var max_steering_angle := 1.0

var _current_index := 0
var _navigation_agent: NavigationAgent2D
var _car: Car2D

func _ready():
	_car = get_parent() as Car2D
	_navigation_agent = NavigationAgent2D.new()
	add_child(_navigation_agent)
	_navigation_agent.path_desired_distance = 60.0
	_navigation_agent.target_desired_distance = 40.0
	_set_next_target()

func get_controls() -> Dictionary:
	if waypoints.is_empty():
		return _no_input()
	
	if _reached_current_waypoint():
		_advance_to_next_waypoint()
	
	var next_point := _navigation_agent.get_next_path_position()
	var desired_dir := (next_point - _car.position).normalized()
	var angle := _car._forward_dir().angle_to(desired_dir)
	
	return {
		"throttle": _compute_throttle(angle),
		"brake": _compute_brake(angle),
		"steer": clamp(angle / max_steering_angle, -1.0, 1.0)
	}

func _reached_current_waypoint() -> bool:
	return _car.position.distance_to(waypoints[_current_index]) < waypoint_radius

func _advance_to_next_waypoint():
	_current_index = wrap(_current_index + 1, 0, waypoints.size())
	_set_next_target()

func _set_next_target():
	if waypoints.size() > 0:
		_navigation_agent.target_position = waypoints[_current_index]

func _compute_throttle(angle: float) -> float:
	if abs(angle) > 2.5:
		return 0.0
	return 1.0 if abs(angle) < 0.5 else 0.3

func _compute_brake(angle: float) -> float:
	return 1.0 if abs(angle) > 2.5 else 0.0

func _no_input() -> Dictionary:
	return { "throttle": 0.0, "brake": 0.0, "steer": 0.0 }
