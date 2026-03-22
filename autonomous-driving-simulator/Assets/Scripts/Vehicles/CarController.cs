using UnityEngine;

public class CarController : MonoBehaviour
{
    public float acceleration = 8f;
    public float steering = 120f;
    public float maxSpeed = 30f;
    public float damping = 1f;

    private Rigidbody2D rb;

    void Start()
    {
        rb = GetComponent<Rigidbody2D>();
        rb.linearDamping = damping;
    }

    void FixedUpdate()
    {
        float move = Input.GetAxis("Vertical");
        float turn = Input.GetAxis("Horizontal");

        // Движение
        if (rb.linearVelocity.magnitude < maxSpeed)
        {
            rb.AddForce(transform.up * move * acceleration);
        }

        // Скорость вдоль направления машины
        float forwardSpeed = Vector2.Dot(rb.linearVelocity, transform.up);

        // Поворот только если есть движение
        if (Mathf.Abs(forwardSpeed) > 0.1f)
        {
            float direction = forwardSpeed > 0 ? 1f : -1f;
            float steeringFactor = Mathf.Clamp01(rb.linearVelocity.magnitude / maxSpeed);
            rb.MoveRotation(rb.rotation - turn * steering * steeringFactor * direction * Time.fixedDeltaTime);
        }

        // Убираем боковое скольжение
        Vector2 forward = transform.up * Vector2.Dot(rb.linearVelocity, transform.up);
        Vector2 sideways = transform.right * Vector2.Dot(rb.linearVelocity, transform.right);

        rb.linearVelocity = forward + sideways * 0.1f;
    }
}
