using UnityEngine;
using UnityEngine.Events;

/// <summary>
/// Обрабатывает столкновения и генерирует события.
/// </summary>
public class CollisionDetector : MonoBehaviour
{
    [Header("Настройки")]
    [Tooltip("Включено ли обнаружение столкновений")]
    [SerializeField] private bool isEnabled = true;

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

    private void OnCollisionEnter2D(Collision2D collision)
    {
        if (!isEnabled) return;

        HandleCollision(collision);
    }

    /// <summary>
    /// Обрабатывает столкновение и вызывает события.
    /// </summary>
    private void HandleCollision(Collision2D collision)
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
    private bool IsCar(GameObject obj)
    {
        return obj.CompareTag("Car");
    }

    // ========== Публичные методы для тестирования ==========

    // Вспомогательный класс для имитации столкновения (только для тестов)
    public class TestCollision : Collision2D
    {
        private GameObject gameObjectOverride;
        
        public TestCollision(GameObject obj)
        {
            gameObjectOverride = obj;
        }
        
        public new GameObject gameObject => gameObjectOverride;
    }
    
    public void TestHandleCollision(GameObject other)
    {
        // Создаем простую имитацию столкновения
        var collision = new TestCollision(other);
        HandleCollision(collision);
    }

    public bool TestIsCar(GameObject obj)
    {
        return IsCar(obj);
    }
}