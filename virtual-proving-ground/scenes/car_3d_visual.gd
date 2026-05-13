extends Node3D

## Ссылка на 2D-машину из world.gd
var target_2d: Car2D 

## Коэффициент масштаба из ScenarioLoader [cite: 1]
const SCALE_FACTOR: float = 10.0 

func _process(_delta: float):
	if is_instance_valid(target_2d):
		# 1. Синхронизируем позицию
		# В 2D: x, y[cite: 5, 6]. В 3D: x, z. 
		# Делим на 100, так как PIXELS_PER_METER = 100 [cite: 11]
		var x_3d = target_2d.global_position.x / 100.0
		var z_3d = target_2d.global_position.y / 100.0
		
		# Высота (Y) остается 0, так как мы на плоскости
		global_position = Vector3(x_3d, 0.0, z_3d)
		
		# 2. Синхронизируем поворот
		# heading_rad в 2D соответствует повороту вокруг оси Y в 3D [cite: 13, 14]
		# В Godot 3D стандартно перед машины смотрит в -Z. 
		# Возможно, понадобится добавить/отнять PI/2 (90 градусов), 
		# если модель развернута боком.
		global_rotation.y = -target_2d.heading_rad
		
		# 3. Бонус: Вращение колес (визуал)
		# Если хочешь, чтобы колеса крутились, можно найти их в меше:
		_animate_wheels(_delta)

func _animate_wheels(_delta):
	# Это упрощенный пример, если у меша есть узлы колес
	# Скорость берем из target_2d.speed_ms [cite: 12]
	var wheel_speed = target_2d.speed_ms * _delta * 5.0
	for wheel in get_tree().get_nodes_in_group("wheels_of_" + str(get_instance_id())):
		wheel.rotate_x(wheel_speed)
