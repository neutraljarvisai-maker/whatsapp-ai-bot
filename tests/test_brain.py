import unittest
from unittest.mock import patch, MagicMock
from core.brain import JarvisBrain

class TestJarvisBrain(unittest.TestCase):
    def setUp(self):
        self.brain = JarvisBrain()

    @patch('google.generativeai.ChatSession.send_message')
    def test_process_user_message_unified(self, mock_send):
        mock_send.return_value.text = '{"intent": "GREETING", "response": "Hello Master Wayne", "facts": {}, "event": {}}'
        result = self.brain.process_user_message("Instruction", "Hello Vecta", "Context")
        self.assertEqual(result['intent'], "GREETING")
        self.assertEqual(result['response'], "Hello Master Wayne")

if __name__ == '__main__':
    unittest.main()
