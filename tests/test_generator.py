# tests/test_generator.py
import unittest
from unittest.mock import patch, MagicMock
import asyncio
from pydantic import ValidationError

from app.models import GenerateRequest
from app.generator import SiteGenerator

class TestApp(unittest.TestCase):

    def test_generate_request_validation_ok(self):
        """Перевірка успішної валідації коректного запиту."""
        data = {
            "topic": "Valid Topic",
            "pages_count": 2,
            "style": "creative"
        }
        try:
            GenerateRequest(**data)
        except ValidationError as e:
            self.fail(f"GenerateRequest raised ValidationError unexpectedly: {e}")

    def test_generate_request_validation_fail(self):
        """Перевірка помилки валідації для некоректного стилю."""
        with self.assertRaises(ValidationError):
            GenerateRequest(topic="Test", style="invalid_style")
            
        with self.assertRaises(ValidationError):
            GenerateRequest(topic="t", style="educational") # Topic too short

    @patch('app.generator.inference')
    @patch('app.generator.inference_image')
    def test_generate_one_site_mocked(self, mock_inference_image, mock_inference):
        """Тестування генерації одного сайту з імітацією API."""
        
        # Налаштування моків
        # 1. Мок для планування
        mock_plan_response = {
            "generated_text": """
            {
                "title": "Mocked Title for LLMs",
                "meta_description": "Mocked meta.",
                "image_prompt": "Mocked image prompt.",
                "sections": [{"heading": "Intro", "brief": "Brief intro."}]
            }
            """
        }
        # 2. Мок для написання контенту
        mock_write_response = {
            "generated_text": "### Intro\nThis is mocked content for the introduction."
        }
        
        mock_inference.side_effect = [mock_plan_response, mock_write_response]
        mock_inference_image.return_value = MagicMock() # Імітуємо успішну генерацію зображення

        # Запуск тесту
        generator = SiteGenerator()
        
        # Використовуємо asyncio.run для асинхронної функції
        result = asyncio.run(generator.generate_one_site(
            topic="LLMs",
            style="technical",
            temperature=0.7,
            top_p=0.9,
            max_tokens=1000,
            generate_image=False # Вимикаємо, щоб не створювати файли
        ))
        
        # Перевірки
        self.assertIn("site_id", result)
        self.assertEqual(result["title"], "Mocked Title for LLMs")
        self.assertEqual(result["sections_count"], 1)
        self.assertEqual(mock_inference.call_count, 2) # Один виклик для плану, один для тексту

if __name__ == '__main__':
    unittest.main()