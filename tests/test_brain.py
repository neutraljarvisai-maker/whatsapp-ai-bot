import unittest
from unittest.mock import patch, MagicMock
from core.brain import JarvisBrain

class TestJarvisBrain(unittest.TestCase):
    def setUp(self):
        self.brain = JarvisBrain()

    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_classify_intent_greeting(self, mock_gen):
        mock_gen.return_value.text = "GREETING"
        intent = self.brain.classify_intent("Hello Jarvis", "No context")
        self.assertEqual(intent, "GREETING")

    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_classify_intent_task(self, mock_gen):
        mock_gen.return_value.text = "TASK"
        intent = self.brain.classify_intent("Open chrome and search for batman", "No context")
        self.assertEqual(intent, "TASK")

    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_extract_facts(self, mock_gen):
        mock_gen.return_value.text = '{"name": "Bruce Wayne", "location": "Gotham"}'
        facts = self.brain.extract_facts("My name is Bruce Wayne and I live in Gotham", "Acknowledged.", "", ["name", "location"])
        self.assertEqual(facts['name'], "Bruce Wayne")
        self.assertEqual(facts['location'], "Gotham")

if __name__ == '__main__':
    unittest.main()
