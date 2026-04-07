using UnityEngine;
using UnityEngine.Events;

/// <summary>
/// Обрабатывает столкновения и генерирует события.
/// </summary>
public class CollisionDetector : MonoBehaviour
{
    [Header("Настройки")]
    [Tooltip("Включено ли обнаружение столкновений")]
    [SerializeField] bool isEnabled = true;

    [Header("События")]
    [Tooltip("Событие при любом столкновении")]
    [SerializeField] private UnityEvent<Collision2D> onCollision;

    [Tooltip("Событие при столкновении с другой машиной")]
    [SerializeField] private UnityEvent<GameObject> onCarCollision;

    /// <summary>
    /// Включена ли обработка столкновений.
    /// </summary>
    public bool IsEnabled
    {
        get => isEnabled;
        set => isEnabled = value;
    }

    /// <summary>
    /// Событие при любом столкновении.
    /// </summary>
    public UnityEvent<Collision2D> OnCollision => onCollision;

    /// <summary>
    /// Событие при столкновении с другой машиной.
    /// </summary>
    public UnityEvent<GameObject> OnCarCollision => onCarCollision;

    internal void OnCollisionEnter2D(Collision2D collision)
    {
        if (!isEnabled) return;

        HandleCollision(collision);
    }

    /// <summary>
    /// Обрабатывает столкновение и вызывает события.
    /// </summary>
    internal void HandleCollision(Collision2D collision)
    {
        Debug.Log($"Столкновение с: {collision.gameObject.name}");

        onCollision?.Invoke(collision);

        if (IsCar(collision.gameObject))
        {
            Debug.Log("Столкновение с другой машиной!");
            onCarCollision?.Invoke(collision.gameObject);
        }
    }

    /// <summary>
    /// Проверяет, является ли объект автомобилем.
    /// </summary>
    internal bool IsCar(GameObject obj)
    {
        return obj.CompareTag("Car");
    }
}