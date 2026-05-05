extends Node
class_name AICarController

@export var waypoints: Array[Vector2] = []
@export var waypoint_radius := 80.0          # расстояние, при котором считаем точку достигнутой
@export var max_steering_angle := 1.0        # ограничение поворота

var _current_waypoint_index := 0
var _navigation_agent: NavigationAgent2D
var _car: Car2D

func _ready():
	_car = get_parent() as Car2D
	_navigation_agent = NavigationAgent2D.new()
	add_child(_navigation_agent)
	# Критически важно: NavigationAgent2D должен быть на том же слое, что и машина
	_navigation_agent.path_desired_distance = 60.0
	_navigation_agent.target_desired_distance = 40.0
	if waypoints.size() > 0:
		_navigation_agent.target_position = waypoints[0]

func get_controls() -> Dictionary:
	"""
	Возвращает словарь с управляющими сигналами:
	{ "throttle": float, "brake": float, "steer": float }
	"""
	if waypoints.is_empty():
		return { "throttle": 0.0, "brake": 0.0, "steer": 0.0 }
	
	# Если достигли текущей точки — переключаемся на следующую
	if _car.position.distance_to(waypoints[_current_waypoint_index]) < waypoint_radius:
		_current_waypoint_index = (_current_waypoint_index + 1) % waypoints.size()
		_navigation_agent.target_position = waypoints[_current_waypoint_index]
	
	# Получаем следующий пункт маршрута от агента
	var next_point = _navigation_agent.get_next_path_position()
	
	# Вектор к цели
	var desired_direction = (next_point - _car.position).normalized()
	var forward = _car._forward_dir()
	
	# Угол между направлением машины и желаемым направлением
	var angle = forward.angle_to(desired_direction)
	
	# Преобразуем угол в steer (-1..1)
	var steer = clamp(angle / max_steering_angle, -1.0, 1.0)
	
	# Если угол большой — замедляемся, иначе едем вперёд
	var throttle = 1.0 if abs(angle) < 0.5 else 0.3
	var brake = 0.0
	if abs(angle) > 2.5:
		throttle = 0.0
		brake = 1.0
	
	return { "throttle": throttle, "brake": brake, "steer": steer }
