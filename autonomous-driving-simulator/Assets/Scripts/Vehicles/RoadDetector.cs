using UnityEngine;

public class RoadDetector : MonoBehaviour
{
    public LayerMask roadLayer;
    public Transform[] checkPoints; // точки проверки (углы машины)
    public float checkRadius = 0.2f;

    public bool isOnRoad;

    void Update()
    {
        int onRoadCount = 0;

        foreach (var point in checkPoints)
        {
            Collider2D hit = Physics2D.OverlapCircle(point.position, checkRadius, roadLayer);
            if (hit != null)
                onRoadCount++;
        }

        isOnRoad = onRoadCount == 4;

        if (!isOnRoad)
            Debug.Log("ВНЕ дороги");
    }
}
