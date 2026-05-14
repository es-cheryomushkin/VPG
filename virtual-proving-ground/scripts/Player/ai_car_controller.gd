extends Node

## Controls a [Car2D] to follow a cyclic path of waypoints using NavigationAgent2D.
class_name AICarController

## List of world positions the car will visit in order, looping back to the first.
@export var waypoints: Array[Vector2] = []
## Distance from a waypoint at which it is considered reached (pixels).
@export var waypoint_radius := 120.0
## Limits how sharply the car can turn toward its target.
@export var max_steering_angle := 1.0

var _current_index := 0
var _navigation_agent: NavigationAgent2D
var _car: Car2D


func _ready():
	_car = get_parent() as Car2D
	_navigation_agent = NavigationAgent2D.new()
	add_child(_navigation_agent)
	# How close the agent tries to stay to the ideal path
	_navigation_agent.path_desired_distance = 60.0
	# How close to the final target before considering it reached
	_navigation_agent.target_desired_distance = 40.0
	_set_next_target()


## Called by [Car2D] every physics frame when this controller is active.
## Returns a dict with "throttle", "brake", and "steer" values in [0..1] range.
func get_controls() -> Dictionary:
	if waypoints.is_empty():
		return _no_input()
	
	if _reached_current_waypoint():
		_advance_to_next_waypoint()
	
	# Get the next point along the navigation path (may differ from waypoint
	# if the agent is steering around an obstacle)
	var next_point := _navigation_agent.get_next_path_position()
	var desired_dir := (next_point - _car.position).normalized()
	var angle := _car._forward_dir().angle_to(desired_dir)
	
	return {
		"throttle": _compute_throttle(angle),
		"brake": _compute_brake(angle),
		"steer": clamp(angle / max_steering_angle, -1.0, 1.0)
	}


## Check if the car is close enough to the current waypoint
func _reached_current_waypoint() -> bool:
	return _car.position.distance_to(waypoints[_current_index]) < waypoint_radius


## Move to the next waypoint, wrapping around to the first
func _advance_to_next_waypoint():
	_current_index = wrap(_current_index + 1, 0, waypoints.size())
	_set_next_target()


## Update the navigation agent's target to the current waypoint
func _set_next_target():
	if waypoints.size() > 0:
		_navigation_agent.target_position = waypoints[_current_index]


## Throttle control: full speed when facing the target, reduced when turning,
## zero when the target is behind the car
func _compute_throttle(angle: float) -> float:
	if abs(angle) > 2.5:
		return 0.0         # Target is behind — stop
	return 1.0 if abs(angle) < 0.5 else 0.3   # Full or reduced throttle


## Brake control: only brake when the target is far behind (sharp turn needed)
func _compute_brake(angle: float) -> float:
	return 1.0 if abs(angle) > 2.5 else 0.0


## Return neutral controls (car stays still)
func _no_input() -> Dictionary:
	return { "throttle": 0.0, "brake": 0.0, "steer": 0.0 }
