using NUnit.Framework;
using UnityEngine;

public class RoadDetectorTests
{
    private GameObject roadObject;
    private GameObject carObject;
    private RoadDetector detector;
    private Transform[] checkPoints;

    [SetUp]
    public void Setup()
    {
        // Создаем дорогу с коллайдером
        roadObject = new GameObject("Road");
        var roadCollider = roadObject.AddComponent<BoxCollider2D>();
        roadCollider.size = new Vector2(10, 10);
        
        // Создаем машину с детектором
        carObject = new GameObject("TestCar");
        detector = carObject.AddComponent<RoadDetector>();
        
        // Создаем 4 точки проверки (углы машины)
        checkPoints = new Transform[4];
        for (int i = 0; i < 4; i++)
        {
            var point = new GameObject($"CheckPoint_{i}");
            point.transform.parent = carObject.transform;
            checkPoints[i] = point.transform;
        }
        
        // Устанавливаем позиции точек (квадрат 1x1)
        checkPoints[0].localPosition = new Vector2(-0.5f, 0.5f);  // левый верхний
        checkPoints[1].localPosition = new Vector2(0.5f, 0.5f);   // правый верхний
        checkPoints[2].localPosition = new Vector2(-0.5f, -0.5f);  // левый нижний
        checkPoints[3].localPosition = new Vector2(0.5f, -0.5f);   // правый нижний
        
        // Устанавливаем точки и радиус в детектор
        detector.SetCheckPoints(checkPoints);
        detector.SetCheckRadius(0.2f);
        detector.SetRoadLayer(LayerMask.GetMask("Default"));
        
        Debug.Log("=== Начало теста RoadDetector ===");
    }

    [TearDown]
    public void Teardown()
    {
        Object.DestroyImmediate(roadObject);
        Object.DestroyImmediate(carObject);
        Debug.Log("=== Конец теста RoadDetector ===\n");
    }

    [Test]
    public void Update_КогдаМашинаНаДороге_IsOnRoadРавноTrue()
    {
        Debug.Log("Тест: Проверка определения нахождения на дороге");
        
        // Ставим машину на дорогу
        carObject.transform.position = Vector3.zero;
        Debug.Log($"  Позиция машины: {carObject.transform.position}");
        
        // Вызываем тестовый метод Update
        detector.TestUpdate();
        
        Debug.Log($"  Результат IsOnRoad: {detector.IsOnRoad}");
        
        Assert.IsTrue(detector.IsOnRoad, 
            "Когда машина на дороге, IsOnRoad должно быть true!");
        
        Debug.Log("  ✓ Тест пройден!");
    }
    
    [Test]
    public void Update_КогдаМашинаВнеДороги_IsOnRoadРавноFalse()
    {
        Debug.Log("Тест: Проверка определения вне дороги");
        
        // Ставим машину вне дороги
        carObject.transform.position = new Vector3(20, 20, 0);
        Debug.Log($"  Позиция машины: {carObject.transform.position}");
        
        // Вызываем тестовый метод Update
        detector.TestUpdate();
        
        Debug.Log($"  Результат IsOnRoad: {detector.IsOnRoad}");
        
        Assert.IsFalse(detector.IsOnRoad, 
            "Когда машина вне дороги, IsOnRoad должно быть false!");
        
        Debug.Log("  ✓ Тест пройден!");
    }
}