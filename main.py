import requests
import time
from datetime import datetime
from flask import Flask, jsonify, request
import threading

app = Flask(__name__)

report_configs = {}

user_data_storage = {}
blacklist = set()
date_format = "%Y-%m-%dT%H:%M"


def format_date_string(date_string):
    dash_count = 0
    formatted_date_string = ''
    for char in date_string:
        if char == '-':
            dash_count += 1
        if dash_count == 3:
            formatted_date_string += 'T'
            dash_count = 0
        else:
            formatted_date_string += char
    return formatted_date_string


def fetch_user_data(page_number):
    try:
        response = requests.get(f"https://sef.podkolzin.consulting/api/users/lastSeen?offset={page_number}")
        data = response.json()
        return data
    except Exception as e:
        print("Error when fetching user data:", repr(e))
        return None


def process_user_data(data):
    if not isinstance(data, dict) or 'data' not in data:
        print("Incorrect data format:", data)
        return

    user_list = data['data']
    for user_info in user_list:
        user_id = user_info.get('userId')
        is_online = user_info.get('isOnline')
        last_seen_str = user_info.get('lastSeenDate')
        current_time = datetime.now().strftime(date_format)

        if user_id in blacklist:
            continue
        if user_id not in user_data_storage:
            user_data_storage[user_id] = []

        last_intervals = user_data_storage[user_id]

        if is_online:
            if not last_intervals or (last_intervals and last_intervals[-1][1] is not None):
                user_data_storage[user_id].append([current_time, None])
        else:
            parts = last_seen_str.split(':')
            last_seen_str = ":".join(parts[:2])
            last_seen_datetime = datetime.strptime(last_seen_str, date_format)
            if last_intervals and last_intervals[-1][1] is None:
                last_intervals[-1][1] = last_seen_datetime
            else:
                user_data_storage[user_id].append([current_time, last_seen_datetime])


def update_user_data():
    page_number = 1
    while True:
        data = fetch_user_data(page_number)
        if data is None:

            pass
        else:
            process_user_data(data)

        if len(data.get('data', [])) > 0:
            page_number += 1
        else:
            break

        print("Waiting 30 seconds before the next attempt....")
        time.sleep(30)


@app.route('/user_intervals', methods=['GET'])
def get_user_intervals():
    return jsonify({user_id: intervals for user_id, intervals in user_data_storage.items() if user_id not in blacklist})


@app.route('/api/stats/user/total', methods=['GET'])
def get_total_user_online_time():
    user_id = request.args.get('userId')
    response = calculate_total_user_online_time(user_id)
    return jsonify(response)


@app.route('/api/stats/user/average', methods=['GET'])
def get_user_average_time():
    user_id = request.args.get('userId')
    response = calculate_user_average_time(user_id)
    return jsonify(response)


@app.route('/api/user/forget', methods=['POST'])
def forget_user():
    user_id = request.args.get('userId')
    response = forget_user_data(user_id)
    return jsonify(response)


@app.route('/api/report/<report_name>', methods=['POST'])
def create_report(report_name):
    report_config = request.get_json()
    report_configs[report_name] = report_config
    return jsonify({})


@app.route('/api/report/<report_name>', methods=['GET'])
def get_report(report_name):
    report_config = report_configs.get(report_name)

    if not report_config:
        return jsonify({"error": "Report not found."}), 404

    from_date = request.args.get('from')
    to_date = request.args.get('to')

    if not from_date or not to_date:
        return jsonify({"error": "Both 'from' and 'to' date parameters are required."}), 400

    report_data = generate_report(report_config, from_date, to_date)

    return jsonify(report_data)


def generate_report(report_config, from_date, to_date):
    metrics = report_config.get("metrics")
    user_ids = report_config.get("users")

    report_data = []

    for user_id in user_ids:
        user_metrics = []

        for metric in metrics:
            if metric == "dailyAverage":

                daily_average_data = calculate_user_average_time(user_id, from_date, to_date, "daily")
                user_metrics.append(daily_average_data)

            elif metric == "total":

                total_time_data = calculate_user_average_time(user_id, from_date, to_date, "total")
                user_metrics.append(total_time_data)

            elif metric == "weeklyAverage":

                weekly_average_data = calculate_user_average_time(user_id, from_date, to_date, "weekly")
                user_metrics.append(weekly_average_data)
            elif metric == "min":

                min_time = calculate_user_min(user_id, from_date, to_date)
                user_metrics.append({"min": min_time})

            elif metric == "max":

                max_time = calculate_user_max(user_id, from_date, to_date)
                user_metrics.append({"max": max_time})

        report_data.append({"userId": user_id, "metrics": user_metrics})

    return report_data


def calculate_user_min(user_id, from_date, to_date):
    user_intervals = user_data_storage.get(user_id, [])
    min_time = float('inf')

    for interval in user_intervals:
        start_time, end_time = interval
        start_time = parse_date(start_time)
        end_time = parse_date(end_time) if end_time else datetime.now()

        if end_time < parse_date(from_date) or start_time > parse_date(to_date):
            continue

        daily_start = max(start_time, parse_date(from_date))
        daily_end = min(end_time, parse_date(to_date))
        daily_duration = (daily_end - daily_start).total_seconds()
        min_time = min(min_time, daily_duration)

    return int(min_time)


def calculate_user_max(user_id, from_date, to_date):
    user_intervals = user_data_storage.get(user_id, [])
    max_time = 0

    for interval in user_intervals:
        start_time, end_time = interval
        start_time = parse_date(start_time)
        end_time = parse_date(end_time) if end_time else datetime.now()

        if end_time < parse_date(from_date) or start_time > parse_date(to_date):
            continue

        daily_start = max(start_time, parse_date(from_date))
        daily_end = min(end_time, parse_date(to_date))
        daily_duration = (daily_end - daily_start).total_seconds()
        max_time = max(max_time, daily_duration)

    return int(max_time)


def calculate_total_user_online_time(user_id):
    if user_id in blacklist:
        return {"error": "User ID is in the blacklist and has been forgotten."}

    user_intervals = user_data_storage.get(user_id, [])
    total_time_seconds = 0

    for interval in user_intervals:
        start_time, end_time = interval

        start_time = parse_date(start_time)
        end_time = parse_date(end_time) if end_time else datetime.now()

        if end_time <= start_time:
            total_time_seconds += (start_time - end_time).total_seconds()

    return {"totalTime": int(total_time_seconds)}


def calculate_user_average_time(user_id, from_date, to_date, metric_type):
    if user_id in blacklist:
        return {"error": "User ID is in the blacklist and has been forgotten."}

    user_intervals = user_data_storage.get(user_id, [])
    total_time_seconds = 0

    for interval in user_intervals:
        start_time, end_time = interval

        start_time = parse_date(start_time)
        end_time = parse_date(end_time) if end_time else datetime.now()

        if end_time <= start_time:
            total_time_seconds += (start_time - end_time).total_seconds()

    num_intervals = len(user_intervals)

    if num_intervals > 0:
        total_days = (end_time - parse_date(user_intervals[0][0])).days + 1
        total_weeks = total_days // 7

        if metric_type == "daily":
            average_time = total_time_seconds / num_intervals
        elif metric_type == "total":
            average_time = total_time_seconds
        elif metric_type == "weekly":
            average_time = total_time_seconds / (total_weeks + 1)
        else:
            return {"error": "Invalid metric_type"}

        return {
            metric_type: int(average_time)
        }
    else:
        return {
            metric_type: 0
        }


def forget_user_data(user_id):
    if user_id:
        blacklist.add(user_id)
        if user_id in user_data_storage:
            del user_data_storage[user_id]
        return {"userId": user_id}
    else:
        return {"error": "Missing 'userId' parameter in the request."}


def parse_date(date_string):
    if isinstance(date_string, str):
        return datetime.strptime(date_string, date_format)
    else:
        return date_string


if __name__ == '__main__':
    data_update_thread = threading.Thread(target=update_user_data)
    data_update_thread.daemon = True
    data_update_thread.start()
    app.run(debug=True)