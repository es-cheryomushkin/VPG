using UnityEngine;
using UnityEngine.Events;

/// <summary>
/// Определяет, находится ли автомобиль на дороге, проверяя контрольные точки.
/// </summary>
public class RoadDetector : MonoBehaviour
{
    [Header("Настройки детекции")]
    [Tooltip("Слой, на котором находится дорога")]
    [SerializeField] private LayerMask roadLayer;

    [Tooltip("Точки проверки (углы автомобиля)")]
    [SerializeField] private Transform[] checkPoints;

    [Tooltip("Радиус проверки каждой точки")]
    [SerializeField] private float checkRadius = 0.2f;

    [Header("События")]
    [Tooltip("Событие при въезде на дорогу")]
    [SerializeField] private UnityEvent onEnterRoad;

    [Tooltip("Событие при съезде с дороги")]
    [SerializeField] private UnityEvent onExitRoad;

    private bool wasOnRoad = true;

    /// <summary>
    /// Находится ли автомобиль на дороге в данный момент.
    /// </summary>
    public bool IsOnRoad { get; private set; }

    /// <summary>
    /// Событие при въезде на дорогу.
    /// </summary>
    public UnityEvent OnEnterRoad => onEnterRoad;

    /// <summary>
    /// Событие при съезде с дороги.
    /// </summary>
    public UnityEvent OnExitRoad => onExitRoad;

    private void Update()
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
    private bool CheckIfOnRoad()
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
    private bool IsPointOnRoad(Vector2 position)
    {
        return Physics2D.OverlapCircle(position, checkRadius, roadLayer) != null;
    }

    /// <summary>
    /// Обрабатывает смену состояния нахождения на дороге.
    /// </summary>
    /// <param name="isOnRoad">Новое состояние нахождения на дороге</param>
    private void HandleStateChanged(bool isOnRoad)
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

    // ========== Публичные методы для тестирования ==========
    public void TestUpdate()
    {
        Update();
    }

    public bool TestCheckIfOnRoad()
    {
        return CheckIfOnRoad();
    }

    public bool TestIsPointOnRoad(Vector2 position)
    {
        return IsPointOnRoad(position);
    }

    public void SetCheckPoints(Transform[] points)
    {
        checkPoints = points;
    }

    public void SetCheckRadius(float radius)
    {
        checkRadius = radius;
    }

    public void SetRoadLayer(LayerMask layer)
    {
        roadLayer = layer;
    }
}