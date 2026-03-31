using NUnit.Framework;
using UnityEngine;

public class CarControllerTests
{
    private GameObject carObject;
    private CarController controller;
    private Rigidbody2D rb;

    [SetUp]
    public void Setup()
    {
        // Создаем тестовую машину
        carObject = new GameObject("TestCar");
        controller = carObject.AddComponent<CarController>();
        rb = carObject.AddComponent<Rigidbody2D>();
        
        // Устанавливаем максимальную скорость
        controller.MaxSpeed = 50f;
        
        controller.SetRigidbody(rb);
        
        Debug.Log("=== Начало теста CarController ===");
    }

    [TearDown]
    public void Teardown()
    {
        Object.DestroyImmediate(carObject);
        Debug.Log("=== Конец теста CarController ===\n");
    }

    [Test]
    public void LimitSpeed_КогдаСкоростьБольшеМаксимальной_ОграничиваетСкорость()
    {
        Debug.Log("Тест: Проверка ограничения скорости");
        
        // Устанавливаем скорость больше максимальной
        rb.linearVelocity = Vector2.up * 100f;
        Debug.Log($"  До вызова LimitSpeed: скорость = {rb.linearVelocity.magnitude} (макс: 50)");
        
        // Вызываем тестовый метод
        controller.TestLimitSpeed();
        
        Debug.Log($"  После вызова LimitSpeed: скорость = {rb.linearVelocity.magnitude}");
        
        // Проверяем, что скорость стала 50
        Assert.AreEqual(50f, rb.linearVelocity.magnitude, 0.1f, 
            $"Скорость должна быть 50, но сейчас {rb.linearVelocity.magnitude}");
        
        Debug.Log("  ✓ Тест пройден!");
    }
}