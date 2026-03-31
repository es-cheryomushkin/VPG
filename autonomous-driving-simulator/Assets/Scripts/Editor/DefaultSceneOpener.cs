using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

[InitializeOnLoad]
public class DefaultSceneOpener
{
    // Укажите путь к вашей сцене
    private static string defaultScenePath = "Assets/Scenes/CarCollisionScene.unity";
    
    static DefaultSceneOpener()
    {
        // Подписываемся на событие загрузки редактора
        EditorApplication.delayCall += OpenDefaultScene;
    }
    
    static void OpenDefaultScene()
    {
        // Проверяем, открыта ли уже какая-то сцена
        if (EditorSceneManager.GetActiveScene().path == "" || 
            EditorSceneManager.GetActiveScene().path == defaultScenePath)
        {
            return;
        }
        
        // Предлагаем открыть сцену по умолчанию
        if (EditorUtility.DisplayDialog("Open Default Scene", 
            $"Открыть сцену {defaultScenePath}?", 
            "Да", "Нет"))
        {
            EditorSceneManager.OpenScene(defaultScenePath);
        }
    }
}