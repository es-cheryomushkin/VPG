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
    [Tooltip("Включена ли система управления машиной")]
    [SerializeField] private bool isEnabled = true;

    [Tooltip("Сила ускорения")]
    [SerializeField] internal float acceleration = 8f;

    [Tooltip("Скорость поворота (град/с)")]
    [SerializeField] internal float steering = 240f;

    [Tooltip("Максимальная скорость машины")]
    [SerializeField] internal float maxSpeed = 60f;

    [Tooltip("Линейное затухание (сопротивление движению)")]
    [SerializeField] internal float damping = 1f;

    [Tooltip("Минимальная скорость для поворота")]
    [SerializeField] internal float minSteeringSpeed = 0.3f;

    [Header("Физика")]
    [Tooltip("Коэффициент бокового трения (0-1). Чем меньше, тем больше скольжения")]
    [SerializeField] internal float lateralFriction = 0.2f;

    [Tooltip("Угловое затухание (сопротивление вращению)")]
    [SerializeField] internal float angularDamping = 2f;

    [Tooltip("Максимальная угловая скорость (град/с)")]
    [SerializeField] internal float maxAngularVelocity = 360f;

    internal Rigidbody2D rb;
    internal InputSystem_Actions input;

    public bool IsEnabled
    {
        get => isEnabled;
        set => isEnabled = value;
    }

    private void Awake()
    {
        input = new InputSystem_Actions();
    }

    private void Start()
    {
        rb = GetComponent<Rigidbody2D>();
        rb.linearDamping = damping;
    }

    private void OnEnable() => input.Enable();
    private void OnDisable() => input.Disable();

    private void FixedUpdate()
    {
        // 1. БАЗОВАЯ ФИЗИКА — выполняется всегда (даже для ботов)
        ApplyPhysics();
        
        // 2. УПРАВЛЕНИЕ — только для игрока
        if (!isEnabled) return;
        
        Vector2 inputVector = input.Player.Move.ReadValue<Vector2>();
        ApplyAcceleration(inputVector.y);
        ApplySteering(inputVector.x);
    }

    /// <summary>
    /// Применяет все базовые физические эффекты.
    /// Выполняется для всех машин, включая ботов.
    /// </summary>
    internal void ApplyPhysics()
    {
        ApplyLateralFriction();
        LimitSpeed();
        ApplyAngularDamping();
        LimitAngularVelocity();
    }

    /// <summary>
    /// Применяет сопротивление вращению (аналог angular drag).
    /// </summary>
    internal void ApplyAngularDamping()
    {
        rb.angularVelocity *= 1f - angularDamping * Time.fixedDeltaTime;
        
        if (Mathf.Abs(rb.angularVelocity) < 5f)
        {
            rb.angularVelocity = 0f;
        }
    }

    /// <summary>
    /// Ограничивает максимальную угловую скорость.
    /// </summary>
    internal void LimitAngularVelocity()
    {
        if (Mathf.Abs(rb.angularVelocity) > maxAngularVelocity)
        {
            rb.angularVelocity = Mathf.Sign(rb.angularVelocity) * maxAngularVelocity;
        }
    }

    /// <summary>
    /// Разгоняет машину, применяя силу в направлении вперед.
    /// </summary>
    internal void ApplyAcceleration(float throttle)
    {
        rb.AddForce(acceleration * throttle * transform.up);
    }

    /// <summary>
    /// Ограничивает максимальную скорость машины.
    /// </summary>
    internal void LimitSpeed()
    {
        if (rb.linearVelocity.magnitude > maxSpeed)
        {
            rb.linearVelocity = rb.linearVelocity.normalized * maxSpeed;
        }
    }

    /// <summary>
    /// Поворачивает машину с учетом текущей скорости и направления движения.
    /// </summary>
    internal void ApplySteering(float turnInput)
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
    internal void ApplyLateralFriction()
    {
        Vector2 forward = transform.up * Vector2.Dot(rb.linearVelocity, transform.up);
        Vector2 sideways = transform.right * Vector2.Dot(rb.linearVelocity, transform.right);

        rb.linearVelocity = forward + sideways * lateralFriction;
    }
}