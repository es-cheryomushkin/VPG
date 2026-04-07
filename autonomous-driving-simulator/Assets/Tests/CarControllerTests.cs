using NUnit.Framework;
using UnityEngine;
using System.Reflection;

public class CarControllerTests
{
    private GameObject carObject;
    private CarController controller;

    [SetUp]
    public void Setup()
    {
        // Создаем тестовую машину
        carObject = new GameObject("TestCar");
        controller = carObject.AddComponent<CarController>();

        // Устанавливаем максимальную скорость
        controller.maxSpeed = 50f;

        controller.rb = carObject.AddComponent<Rigidbody2D>();
        
        Debug.Log("=== Начало теста CarController ===");
    }

    [TearDown]
    public void Teardown()
    {
        Object.DestroyImmediate(carObject);
        Debug.Log("=== Конец теста CarController ===\n");
    }

    [Test]
    public void LimitSpeed_Когда_Скорость_Больше_Максимальной_Ограничивает_Скорость()
    {
        Debug.Log("Тест: Проверка ограничения скорости");
        
        // Устанавливаем скорость больше максимальной
        controller.rb.linearVelocity = Vector2.up * 100f;
        Debug.Log($"  До вызова LimitSpeed: скорость = {controller.rb.linearVelocity.magnitude} (макс: 50)");
        
        // Вызываем тестовый метод
        controller.LimitSpeed();
        
        Debug.Log($"  После вызова LimitSpeed: скорость = {controller.rb.linearVelocity.magnitude}");
        
        // Проверяем, что скорость стала 50
        Assert.AreEqual(50f, controller.rb.linearVelocity.magnitude, 0.1f, 
            $"Скорость должна быть 50, но сейчас {controller.rb.linearVelocity.magnitude}");
        
        Debug.Log("  ✓ Тест пройден!");
    }
}