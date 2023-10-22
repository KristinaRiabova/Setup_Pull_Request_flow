import unittest
from datetime import datetime
from unittest.mock import patch, Mock
from main import (
    format_date_string,
    process_user_data,
    calculate_user_min,
    calculate_user_max,
    calculate_total_user_online_time,
    calculate_user_average_time,
    forget_user_data,
    parse_date,calculate_global_metrics, generate_report
)


class TestFormatDateString(unittest.TestCase):
    def test_format_date_string(self):
        input_date = "2023-10-19-08:30"
        expected_output = "2023-10-19T08:30"
        self.assertEqual(format_date_string(input_date), expected_output)


class TestProcessUserData(unittest.TestCase):
    def test_process_user_data(self):
        data = {"data": [{"userId": 1, "isOnline": True, "lastSeenDate": "2023-10-19T08:30"}]}
        user_data_storage = {}
        process_user_data(data)
        self.assertIn(1, user_data_storage)


class TestCalculateUserMin(unittest.TestCase):
    def test_calculate_user_min(self):
        user_id = 1
        from_date = "2023-10-19T08:00"
        to_date = "2023-10-19T09:00"
        user_data_storage = {1: [("2023-10-19T08:30", "2023-10-19T08:45")]}
        self.assertEqual(calculate_user_min(user_id, from_date, to_date), 15)


class TestCalculateUserMax(unittest.TestCase):
    def test_calculate_user_max(self):
        user_id = 1
        from_date = "2023-10-19T08:00"
        to_date = "2023-10-19T09:00"
        user_data_storage = {1: [("2023-10-19T08:30", "2023-10-19T08:45")]}
        self.assertEqual(calculate_user_max(user_id, from_date, to_date), 15)


class TestCalculateTotalUserOnlineTime(unittest.TestCase):
    def test_calculate_total_user_online_time(self):
        user_id = 1
        user_data_storage = {1: [("2023-10-19T08:30", "2023-10-19T08:45")]}
        self.assertEqual(calculate_total_user_online_time(user_id), {"totalTime": 15})


class TestCalculateUserAverageTime(unittest.TestCase):
    def test_calculate_user_average_time(self):
        user_id = 1
        from_date = "2023-10-19T08:00"
        to_date = "2023-10-19T09:00"
        metric_type = "daily"
        user_data_storage = {1: [("2023-10-19T08:30", "2023-10-19T08:45")]}
        self.assertEqual(calculate_user_average_time(user_id, from_date, to_date, metric_type), {"daily": 15})


class TestForgetUserData(unittest.TestCase):
    def test_forget_user_data(self):
        user_id = 1
        blacklist = set()
        user_data_storage = {1: [("2023-10-19T08:30", "2023-10-19T08:45")]}

        response = forget_user_data(user_id)

        self.assertEqual(response, {"userId": 1})
        self.assertIn(1, blacklist)
        self.assertNotIn(1, user_data_storage)


class TestParseDate(unittest.TestCase):
    def test_parse_date(self):
        date_string = "2023-10-19T08:30"
        expected_date = datetime(2023, 10, 19, 8, 30)
        self.assertEqual(parse_date(date_string), expected_date)



if __name__ == '__main__':
    unittest.main()
