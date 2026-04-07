# Autonomous Driving Simulator - Unity

Симулятор для тестирования алгоритмов автономного вождения в 2D пространстве.

## 📋 Требования

- **Unity 6000.3.11f1** (или новее)
- **Unity Hub** (рекомендуется)
- Пакеты (устанавливаются автоматически):
  - Input System 1.19.0
  - 2D Animation, Sprite, Tilemap и др.

## 🚀 Запуск

### 1. Открытие проекта в Unity

1. Запустите **Unity Hub**
2. Нажмите **Open** → выберите папку `autonomous-driving-simulator`
3. Дождитесь импорта всех пакетов (Unity скачает их автоматически)

### 2. Настройка Input System

При первом открытии появится окно:
> "This project is using the new input system package..."
- Нажмите **Yes** (Unity перезапустится)

## 🎮 Запуск симуляции

### Открытие сцены

1. В окне **Project** перейдите в `Assets/Scenes/`
2. Дважды кликните на `SampleScene.unity`
3. Нажмите **Play** (треугольник) для запуска

### Управление

| Клавиша | Действие |
|---------|----------|
| W / ↑ | Газ (вперёд) |
| S / ↓ | Тормоз / назад |
| A / ← | Поворот влево |
| D / → | Поворот вправо |

### Объекты в сцене

- **Car** — управляемый автомобиль (скрипты: CarController, CollisionDetector, RoadDetector)
- **Road** — дорога (слой Road, триггер для детекции)
- **Global Light 2D** — глобальное освещение

## 🧪 Запуск Unit-тестов

### Через Test Runner

1. **Window → General → Test Runner**
2. Выбрать вкладку **EditMode**
3. Нажать **Run All**

### Тесты проверяют

| Тест | Что проверяет |
|------|---------------|
| `CarControllerTests.LimitSpeed_Когда_Скорость_Больше_Максимальной_Ограничивает_Скорость` | Ограничение максимальной скорости |
| `CollisionDetectorTests.IsCar_КогдаОбъектСТегомCar_ВозвращаетTrue` | Распознавание машины по тегу |
| `CollisionDetectorTests.IsEnabled_МожноВключитьИВыключить` | Включение/выключение детектора |
| `RoadDetectorTests.Update_КогдаМашинаНаДороге_IsOnRoadРавноTrue` | Определение нахождения на дороге |
| `RoadDetectorTests.Update_КогдаМашинаВнеДороги_IsOnRoadРавноFalse` | Определение нахождения вне дороги |

## 📁 Структура проекта

```
Assets/
├── Prefabs/
│   └── Car.prefab               # Префаб автомобиля
├── Scenes/
│   └── SampleScene.unity        # Основная сцена
├── Scripts/
│   ├── CarController.cs         # Управление движением
│   ├── CollisionDetector.cs     # Детектор столкновений
│   ├── RoadDetector.cs          # Детектор дороги
│   ├── GameScripts.asmdef       # Assembly Definition для скриптов
│   └── AssemblyInfo.cs          # InternalsVisibleTo для тестов
├── Settings/                    # Настройки URP
├── Sprites/                     # Визуальные ассеты
└── Tests/
    ├── CarControllerTests.cs    # Тесты управления
    ├── CollisionDetectorTests.cs # Тесты столкновений
    ├── RoadDetectorTests.cs     # Тесты дороги
    └── Tests.asmdef             # Assembly Definition для тестов

Packages/
└── manifest.json                # Зависимости проекта

ProjectSettings/                 # Настройки Unity
```

## 🏎️ Компоненты автомобиля

| Компонент | Описание |
|-----------|----------|
| **CarController** | Управление движением: ускорение, поворот, боковое трение, угловое затухание |
| **CollisionDetector** | Обработка столкновений, генерация событий |
| **RoadDetector** | Проверка нахождения на дороге по контрольным точкам |
| **Rigidbody2D** | Физика (линейное и угловое затухание) |
| **BoxCollider2D** | Коллайдер для столкновений |

## 🛠️ Создание ботов (AI-машин)

Для создания неуправляемых машин:

1. Скопируйте префаб `Car.prefab`
2. На экземпляре отключите управление:
   - `CarController → Is Enabled = false`
