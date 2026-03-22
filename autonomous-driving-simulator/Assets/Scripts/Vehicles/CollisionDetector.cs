using UnityEngine;

public class CollisionDetector : MonoBehaviour
{
    void OnCollisionEnter2D(Collision2D collision)
    {
        Debug.Log("Столкновение с: " + collision.gameObject.name);

        if (collision.gameObject.CompareTag("Car"))
        {
            Debug.Log("Столкновение с другой машиной!");
        }
    }
}