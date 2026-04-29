extends Node
class_name CollisionSolver

@export var restitution : float = 0.2
@export var min_impact_speed : float = 0.5  # м/с

func resolve(
	v_a: Vector2, v_b: Vector2,
	m_a: float, m_b: float,
	normal: Vector2,
	dir_a: Vector2, dir_b: Vector2
) -> Dictionary:
	normal = normal.normalized()
	
	var rel_vel = v_a - v_b
	var vel_along_normal = rel_vel.dot(normal)
	
	# Не столкновение
	if vel_along_normal > 0 or abs(vel_along_normal) < min_impact_speed:
		return {}
	
	# Импульс
	var j = -(1.0 + restitution) * vel_along_normal
	j /= (1.0 / m_a + 1.0 / m_b)
	
	var impulse = j * normal
	
	var v_a_new = v_a + impulse / m_a
	var v_b_new = v_b - impulse / m_b
	
	# Энергия
	var ke_before = 0.5 * m_a * v_a.length_squared() + 0.5 * m_b * v_b.length_squared()
	var ke_after  = 0.5 * m_a * v_a_new.length_squared() + 0.5 * m_b * v_b_new.length_squared()
	var energy_lost = max(0.0, ke_before - ke_after)
	
	# Классификация - ИСПРАВЛЕНО
	var type = _classify(normal, v_a, v_b, dir_a, dir_b)
	var severity = _severity(energy_lost)
	
	return {
		"v_a": v_a_new,
		"v_b": v_b_new,
		"impulse": impulse,
		"energy_lost": energy_lost,
		"type": type,
		"severity": severity
	}

func _classify(normal: Vector2, v_a: Vector2, v_b: Vector2, dir_a: Vector2, dir_b: Vector2) -> String:
	# normal указывает от A к B
	# Проверяем, едут ли машины навстречу
	var a_moving_toward_b = v_a.dot(normal) < 0  # A движется в сторону B
	var b_moving_toward_a = v_b.dot(-normal) < 0  # B движется в сторону A
	
	if a_moving_toward_b and b_moving_toward_a:
		# Обе движутся навстречу - лобовое
		return "head_on"
	
	# Проверяем, догоняет ли A машину B (удар сзади)
	var a_faster_than_b = v_a.length() > v_b.length()
	var same_direction = dir_a.dot(dir_b) > 0.7  # Смотрят примерно в одну сторону
	
	if same_direction and a_faster_than_b and a_moving_toward_b:
		return "rear"
	
	# Всё остальное - боковой удар
	return "side"

func _severity(energy: float) -> String:
	if energy < 5000:
		return "minor"
	if energy < 20000:
		return "medium"
	return "severe"
