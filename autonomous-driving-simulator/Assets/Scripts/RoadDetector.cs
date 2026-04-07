using UnityEngine;
using UnityEngine.Events;

/// <summary>
/// Определяет, находится ли автомобиль на дороге, проверяя контрольные точки.
/// </summary>
public class RoadDetector : MonoBehaviour
{
    [Header("Настройки детекции")]
    [Tooltip("Слой, на котором находится дорога")]
    [SerializeField] 
    internal LayerMask roadLayer;

    [Tooltip("Точки проверки (углы автомобиля)")]
    [SerializeField] internal Transform[] checkPoints;

    [Tooltip("Радиус проверки каждой точки")]
    [SerializeField] internal float checkRadius = 0.2f;

    [Header("События")]
    [Tooltip("Событие при въезде на дорогу")]
    [SerializeField] internal UnityEvent onEnterRoad;

    [Tooltip("Событие при съезде с дороги")]
    [SerializeField] internal UnityEvent onExitRoad;

    internal bool wasOnRoad = true;

    /// <summary>
    /// Находится ли автомобиль на дороге в данный момент.
    /// </summary>
    public bool IsOnRoad { get; internal set; }

    /// <summary>
    /// Событие при въезде на дорогу.
    /// </summary>
    public UnityEvent OnEnterRoad => onEnterRoad;

    /// <summary>
    /// Событие при съезде с дороги.
    /// </summary>
    public UnityEvent OnExitRoad => onExitRoad;

    internal void Update()
    {
        IsOnRoad = CheckIfOnRoad();

        if (IsOnRoad == wasOnRoad) return;

        HandleStateChanged(IsOnRoad);
        wasOnRoad = IsOnRoad;
    }

    /// <summary>
    /// Проверяет, находятся ли все контрольные точки на дороге.
    /// </summary>
    /// <returns>True, если все точки на дороге, иначе False</returns>
    internal bool CheckIfOnRoad()
    {
        if (checkPoints == null || checkPoints.Length == 0)
        {
            Debug.LogWarning($"{nameof(RoadDetector)}: Нет назначенных точек проверки на {gameObject.name}");
            return false;
        }

        int count = 0;

        foreach (Transform point in checkPoints)
        {
            if (point == null) continue;

            if (IsPointOnRoad(point.position))
            {
                count++;
            }
        }

        return count == checkPoints.Length;
    }

    /// <summary>
    /// Проверяет, находится ли точка на дороге.
    /// </summary>
    /// <param name="position">Позиция для проверки</param>
    /// <returns>True, если точка на дороге</returns>
    internal bool IsPointOnRoad(Vector2 position)
    {
        return Physics2D.OverlapCircle(position, checkRadius, roadLayer) != null;
    }

    /// <summary>
    /// Обрабатывает смену состояния нахождения на дороге.
    /// </summary>
    /// <param name="isOnRoad">Новое состояние нахождения на дороге</param>
    internal void HandleStateChanged(bool isOnRoad)
    {
        if (isOnRoad)
        {
            Debug.Log("Машина вернулась на дорогу");
            onEnterRoad?.Invoke();
        }
        else
        {
            Debug.Log("Машина выехала за пределы дороги!");
            onExitRoad?.Invoke();
        }
    }
}