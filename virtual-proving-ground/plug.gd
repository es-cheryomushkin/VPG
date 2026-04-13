extends "res://addons/gd-plug/plug.gd"

func _plugging():
    # Подключаем GUT (уже есть в addons, но для порядка)
    plug("bitwes/Gut")
    plug("imjp94/gd-plug")  # сам gd-plug (проверка)

    # Здесь будут другие зависимости, когда появятся
    # plug("автор/репозиторий")