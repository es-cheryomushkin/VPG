using UnityEngine;
using UnityEngine.InputSystem;

/// <summary>
/// Управляет движением автомобиля в 2D.
/// Машина получает ввод через New Input System, разгоняется силой,
/// поворачивает через angularVelocity и частично гасит боковое скольжение.
/// </summary>
public class CarController : MonoBehaviour
{
    [Header("Параметры движения")]
    [Tooltip("Сила ускорения. Чем выше значение, тем быстрее машина набирает скорость")]
    [SerializeField] private float acceleration = 8f;

    [Tooltip("Скорость поворота. Чем выше значение, тем быстрее машина вращается")]
    [SerializeField] private float steering = 240f;

    [Tooltip("Максимальная скорость машины")]
    [SerializeField] private float maxSpeed = 60f;

    [Tooltip("Линейное затухание Rigidbody2D. Уменьшает скольжение и плавно замедляет машину")]
    [SerializeField] private float damping = 1f;

    [Tooltip("Минимальная скорость для поворота")]
    [SerializeField] private float minSteeringSpeed = 0.3f;

    [Tooltip("Коэффициент бокового трения (0-1). Чем меньше, тем больше скольжения")]
    [SerializeField] private float lateralFriction = 0.2f;
    
    private Rigidbody2D rb;
    private InputSystem_Actions input;

    /// <summary>
    /// Инициализирует систему ввода.
    /// </summary>
    private void Awake()
    {
        input = new InputSystem_Actions();
    }

    /// <summary>
    /// Получает компонент Rigidbody2D и настраивает затухание.
    /// </summary>
    private void Start()
    {
        rb = GetComponent<Rigidbody2D>();
        rb.linearDamping = damping;
    }

    /// <summary>
    /// Включает обработку ввода при активации объекта.
    /// </summary>
    private void OnEnable() => input.Enable();

    /// <summary>
    /// Отключает обработку ввода при деактивации объекта.
    /// </summary>
    private void OnDisable() => input.Disable();

    /// <summary>
    /// Вызывается каждый физический кадр. Обрабатывает движение автомобиля.
    /// </summary>
    private void FixedUpdate()
    {
        Vector2 inputVector = input.Player.Move.ReadValue<Vector2>();

        ApplyAcceleration(inputVector.y);
        LimitSpeed();
        ApplySteering(inputVector.x);
        ApplyLateralFriction();
    }

    /// <summary>
    /// Разгоняет машину, применяя силу в направлении вперед.
    /// </summary>
    /// <param name="throttle">Значение газа от -1 до 1</param>
    private void ApplyAcceleration(float throttle)
    {
        rb.AddForce(acceleration * throttle * transform.up);
    }

    /// <summary>
    /// Ограничивает максимальную скорость машины.
    /// </summary>
    private void LimitSpeed()
    {
        if (rb.linearVelocity.magnitude > maxSpeed)
        {
            rb.linearVelocity = rb.linearVelocity.normalized * maxSpeed;
        }
    }

    /// <summary>
    /// Поворачивает машину с учетом текущей скорости и направления движения.
    /// </summary>
    /// <param name="turnInput">Значение поворота от -1 до 1</param>
    private void ApplySteering(float turnInput)
    {
        float forwardSpeed = Vector2.Dot(rb.linearVelocity, transform.up);

        if (Mathf.Abs(forwardSpeed) < minSteeringSpeed)
        {
            rb.angularVelocity = 0f;
            return;
        }

        float direction = forwardSpeed > 0 ? 1f : -1f;
        float speedFactor = Mathf.Pow(rb.linearVelocity.magnitude / maxSpeed, 0.5f);

        rb.angularVelocity = -turnInput * steering * speedFactor * direction;
    }

    /// <summary>
    /// Уменьшает боковое скольжение, сохраняя продольную скорость.
    /// </summary>
    private void ApplyLateralFriction()
    {
        Vector2 forward = transform.up * Vector2.Dot(rb.linearVelocity, transform.up);
        Vector2 sideways = transform.right * Vector2.Dot(rb.linearVelocity, transform.right);

        rb.linearVelocity = forward + sideways * lateralFriction;
    }

    // ========== Публичные методы для тестирования ==========
    public void TestLimitSpeed()
    {
        LimitSpeed();
    }

    public void TestApplyAcceleration(float throttle)
    {
        ApplyAcceleration(throttle);
    }

    public void TestApplySteering(float turnInput)
    {
        ApplySteering(turnInput);
    }

    public void TestApplyLateralFriction()
    {
        ApplyLateralFriction();
    }

    public float MaxSpeed
    {
        get => maxSpeed;
        set => maxSpeed = value;
    }

    // Метод для установки Rigidbody2D из тестов
    public void SetRigidbody(Rigidbody2D rigidbody)
    {
        rb = rigidbody;
    }
}
