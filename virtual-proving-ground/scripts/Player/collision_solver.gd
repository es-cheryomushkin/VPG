extends Node
class_name CollisionSolver

const DEFAULT_MASS := 1500.0
@export var restitution: float = 0.2
@export var min_impact_speed: float = 0.5

func resolve_collision(body_a: Dictionary, body_b: Dictionary, normal: Vector2) -> Dictionary:
	normal = normal.normalized()
	
	var v_a: Vector2 = body_a.velocity
	var v_b: Vector2 = body_b.velocity
	
	var m_a: float = body_a.get("mass", DEFAULT_MASS)
	var m_b: float = body_b.get("mass", DEFAULT_MASS)
	
	var relative_velocity: Vector2 = v_a - v_b
	var vel_along_normal: float = relative_velocity.dot(normal)
	
	if vel_along_normal > 0:
		return {}
	
	if abs(vel_along_normal) < min_impact_speed:
		return {}
	
	var j: float = -(1.0 + restitution) * vel_along_normal
	j /= (1.0 / m_a + 1.0 / m_b)
	
	var impulse: Vector2 = j * normal
	
	# Новые скорости после удара
	var v_a_new = v_a + impulse / m_a
	var v_b_new = v_b - impulse / m_b
	
	var energy_before = _kinetic_energy(m_a, v_a) + _kinetic_energy(m_b, v_b)
	var energy_after  = _kinetic_energy(m_a, v_a_new) + _kinetic_energy(m_b, v_b_new)
	var energy_lost = max(0.0, energy_before - energy_after)
	
	var type = _classify_collision(normal, body_a, body_b)
	var severity = _classify_severity(energy_lost)
	
	return {
		"impulse": impulse,
		"v_a": v_a_new,
		"v_b": v_b_new,
		"energy_lost": energy_lost,
		"type": type,
		"severity": severity
	}

func _kinetic_energy(m: float, v: Vector2) -> float:
	return 0.5 * m * v.length_squared()

func _classify_collision(normal: Vector2, a: Dictionary, b: Dictionary) -> String:
	# Если передаёте rotation, используйте его
	if a.has("rotation") and b.has("rotation"):
		var forward_a = Vector2.RIGHT.rotated(a.rotation)
		var forward_b = Vector2.RIGHT.rotated(b.rotation)
		var dot_a = forward_a.dot(normal)
		var dot_b = forward_b.dot(-normal)
		if dot_a > 0.7 and dot_b > 0.7:
			return "head_on"
		elif dot_a < -0.7 and dot_b < -0.7:
			return "rear"
	return "side"

func _classify_severity(energy: float) -> String:
	if energy < 5000:
		return "minor"
	elif energy < 20000:
		return "medium"
	else:
		return "severe"
