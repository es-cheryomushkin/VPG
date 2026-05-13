extends "res://addons/gd-plug/plug.gd"

func _plugging():
    # Подключаем GUT (уже есть в addons, но для порядка)
    plug("bitwes/Gut")

    # Здесь будут другие зависимости, когда появятся
    # plug("автор/репозиторий")