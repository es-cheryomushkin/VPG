extends Node2D

@onready var cars = $Cars
var car_scene = preload("res://scenes/playground/cars.tscn")

func spawn_car(pos, initial_velocity = Vector2.ZERO):
	var car = car_scene.instantiate()
	cars.add_child(car)
	car.position = pos
	car.velocity = initial_velocity

func _ready():
	spawn_car(Vector2(-200, -400), Vector2(300, 0))
	#spawn_car(Vector2(200, 400), Vector2(300, 0))
	#spawn_car(Vector2(700, 400), Vector2(300, 0))
	pass
