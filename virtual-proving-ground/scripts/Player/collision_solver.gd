extends Node
class_name CollisionSolver

@export var restitution := 0.2
@export var min_impact_speed := 0.5

func resolve(
	v_a: Vector2, v_b: Vector2,
	m_a: float, m_b: float,
	normal: Vector2,
	dir_a: Vector2, dir_b: Vector2,
	contact_point := Vector2.ZERO
) -> Dictionary:
	normal = normal.normalized()
	var rel_vel := v_a - v_b
	var approach_speed := rel_vel.dot(normal)

	if approach_speed > 0.0 or abs(approach_speed) < min_impact_speed:
		return {}

	var j := -(1.0 + restitution) * approach_speed / (1.0 / m_a + 1.0 / m_b)
	var impulse := j * normal

	var ke_before := _kinetic_energy(m_a, v_a) + _kinetic_energy(m_b, v_b)
	var v_a_new := v_a + impulse / m_a
	var v_b_new := v_b - impulse / m_b
	var ke_after := _kinetic_energy(m_a, v_a_new) + _kinetic_energy(m_b, v_b_new)

	return {
		"v_a": v_a_new,
		"v_b": v_b_new,
		"impulse": impulse,
		"energy_lost": max(0.0, ke_before - ke_after),
		"type": _classify(normal, v_a, v_b, dir_a, dir_b),
		"severity": _severity(ke_before - ke_after),
		"contact_point": contact_point
	}

func _kinetic_energy(m: float, v: Vector2) -> float:
	return 0.5 * m * v.length_squared()

func _classify(normal: Vector2, v_a: Vector2, v_b: Vector2, dir_a: Vector2, dir_b: Vector2) -> String:
	var a_toward_b := v_a.dot(normal) < 0.0
	var b_toward_a := v_b.dot(-normal) < 0.0
	
	if a_toward_b and b_toward_a:
		return "head_on"
	
	var catching_up := v_a.length() > v_b.length() and dir_a.dot(dir_b) > 0.7
	if catching_up and a_toward_b:
		return "rear"
	
	return "side"

func _severity(energy: float) -> String:
	if energy < 5000.0:
		return "minor"
	if energy < 20000.0:
		return "medium"
	return "severe"
