import unittest
import threading
import time
import requests
from main import app

BASE_URL = 'http://localhost:5000'

class TestE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app_thread = threading.Thread(target=app.run, kwargs={'debug': False})
        cls.app_thread.daemon = True
        cls.app_thread.start()
        cls.wait_for_app_to_start()

    @classmethod
    def tearDownClass(cls):
        cls.app_thread.join(timeout=1)

    @classmethod
    def wait_for_app_to_start(cls):
        time.sleep(2)

    def test_get_user_intervals(self):
        response = requests.get(f'{BASE_URL}/user_intervals')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, dict)
        self.assertTrue(all(isinstance(k, str) and isinstance(v, list) for k, v in data.items()))

    def test_get_total_user_online_time(self):
        user_id = '02d4563d-5727-c811-b3b7-57a10f6be25a'
        response = requests.get(f'{BASE_URL}/api/stats/user/total?userId={user_id}')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, dict)
        self.assertIn('totalTime', data)



    def test_create_report(self):
        report_name = 'test_report'
        report_config = {
            'metrics': ['dailyAverage'],
            'users': ['02d4563d-5727-c811-b3b7-57a10f6be25a']
        }
        response = requests.post(f'{BASE_URL}/api/report/{report_name}', json=report_config)
        self.assertEqual(response.status_code, 200)

    def test_get_report(self):
        report_name = 'my_report_name'
        from_date = '2023-10-19'
        to_date = '2023-10-19T18:00'
        response = requests.get(f'{BASE_URL}/api/report/{report_name}', params={'from': from_date, 'to': to_date})
        self.assertEqual(response.status_code, 404)
        data = response.json()




if __name__ == '__main__':
    unittest.main()

