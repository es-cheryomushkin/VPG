using NUnit.Framework;
using UnityEngine;

public class CollisionDetectorTests
{
    private GameObject detectorObject;
    private CollisionDetector detector;
    private GameObject otherCar;
    private bool carCollisionTriggered = false;
    private GameObject triggeredCar = null;

    [SetUp]
    public void Setup()
    {
        // Создаем детектор
        detectorObject = new GameObject("TestDetector");
        detector = detectorObject.AddComponent<CollisionDetector>();
        
        // Создаем другую машину с тегом "Car"
        otherCar = new GameObject("OtherCar");
        otherCar.tag = "Car";
        
        // Сбрасываем флаги
        carCollisionTriggered = false;
        triggeredCar = null;
        
        // Проверяем, что событие не null, и подписываемся
        if (detector.OnCarCollision != null)
        {
            detector.OnCarCollision.AddListener((car) => {
                carCollisionTriggered = true;
                triggeredCar = car;
            });
        }
        
        Debug.Log("=== Начало теста CollisionDetector ===");
    }

    [TearDown]
    public void Teardown()
    {
        Object.DestroyImmediate(detectorObject);
        Object.DestroyImmediate(otherCar);
        Debug.Log("=== Конец теста CollisionDetector ===\n");
    }

    [Test]
    public void IsCar_КогдаОбъектСТегомCar_ВозвращаетTrue()
    {
        Debug.Log("Тест: Проверка определения машины по тегу");
        
        // Вызываем тестовый метод
        bool result = detector.TestIsCar(otherCar);
        
        Debug.Log($"  Объект: {otherCar.name}, тег: {otherCar.tag}");
        Debug.Log($"  Результат IsCar: {result}");
        
        Assert.IsTrue(result, "Объект с тегом Car должен распознаваться как машина!");
        
        Debug.Log("  ✓ Тест пройден!");
    }

    [Test]
    public void IsEnabled_МожноВключитьИВыключить()
    {
        Debug.Log("Тест: Проверка включения/выключения детектора");
        
        // Проверяем выключение
        detector.IsEnabled = false;
        Debug.Log($"  IsEnabled = {detector.IsEnabled}");
        Assert.IsFalse(detector.IsEnabled, "IsEnabled должно быть false!");
        
        // Проверяем включение
        detector.IsEnabled = true;
        Debug.Log($"  IsEnabled = {detector.IsEnabled}");
        Assert.IsTrue(detector.IsEnabled, "IsEnabled должно быть true!");
        
        Debug.Log("  ✓ Тест пройден!");
    }
}