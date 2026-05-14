# Быстрый старт (Quick Start)

## 1. Клонирование

```bash
git clone <repo-url>
cd VPG/virtual-proving-ground
```

## 2. Установка зависимостей

Проект использует **gd-plug** для управления аддонами (GUT и другие).

### Способ А: Автоматически (рекомендуется)

```bash
# Windows (PowerShell)
& "путь_к_godot.exe" --headless -s plug.gd install

# Windows (CMD)
"путь_к_godot.exe" --headless -s plug.gd install

# Linux
./godot --headless -s plug.gd install
```

### Способ Б: Через редактор Godot

1. Откройте проект в Godot (File → Import → укажите папку `virtual-proving-ground`)
2. В верхнем меню: **AssetLib** → поиск **Gut** → **Install**
3. **Project → Project Settings → Plugins** → включите **Gut**

## 3. Запуск сцены

В редакторе Godot:

1. Откройте сцену `res://scenes/playground/playground.scn`
2. Нажмите **F5** (Run Project) или кнопку ▶ в правом верхнем углу

**Управление машиной:**
| Клавиша | Действие |
|---------|----------|
| W / ↑ | Газ (вперёд) |
| S / ↓ | Задний ход |
| A / ← | Поворот влево |
| D / → | Поворот вправо |
| Space | Тормоз |

**Управление сценариями:**
| Клавиша | Действие |
|---------|----------|
| N | Следующий сценарий |
| P | Предыдущий сценарий |
| R | Перезапустить текущий |

## 4. Запуск тестов

```bash
# Через редактор: F10 → выбрать test_collision_solver.gd → Run

# Через консоль:
godot --headless -s addons/gut/gut_cmdln.gd -gtest -gdir=res://scripts/Tests/
```

---

## Структура проекта

```
virtual-proving-ground/
├── addons/                  # Плагины Godot (GUT, gd-plug) — не в репозитории
├── assets/
│   ├── pedestrians/         # Спрайты пешеходов
│   └── vehicles/            # Спрайты машин
├── lib/                     # Сторонние библиотеки
├── scenes/
│   └── playground/          # Основная сцена и её дубликаты
├── scripts/
│   ├── Player/              # Физика машины (Car2D, CollisionSolver)
│   ├── Tests/               # GUT-тесты
│   └── World/               # Управление сценой, загрузчик сценариев
├── plug.gd                  # Конфигурация gd-plug
└── README.md
```

### Дерево сцены (playground.scn)

```
Node2D (world.gd)
├── World
│   ├── Road
│   │   └── TileMapLayer
│   ├── Environment
│   │   ├── Background (Sprite2D)
│   │   └── Lights
│   └── NavigationRegion2D
│   		└── NavigationPolygon (область для AI-навигации)
├── Player
│   └── Car (Car2D)
│       ├── Sprite2D
│       ├── Camera2D
│       ├── CollisionShape2D
│       └── AIController
├── Cars
│   └── ... (машины из сценариев, создаются во время выполнения)
├── CollisionSolver (CollisionSolver)
└── UI
    ├── SpeedLabel
    └── ScenarioLabel
```
