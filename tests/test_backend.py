import unittest
from unittest.mock import patch, MagicMock
from desktop_backend import app

class TestDesktopBackend(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    @patch('desktop_backend.brain.process_user_message')
    @patch('desktop_backend.load_profile')
    def test_chat_endpoint(self, mock_load_profile, mock_process):
        mock_load_profile.return_value = {"name": "Master Wayne"}
        mock_process.return_value = {"intent": "GREETING", "response": "Hello, Master Wayne.", "facts": {}, "event": {}}

        response = self.client.post('/chat', json={
            'user_id': 'test_user',
            'message': 'Hello'
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['response'], "Hello, Master Wayne.")

if __name__ == '__main__':
    unittest.main()
