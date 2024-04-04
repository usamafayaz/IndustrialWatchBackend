from datetime import datetime


def get_formatted_number(type):
    current_datetime = datetime.now()
    date_str = current_datetime.strftime("%d-%m-%Y")  # Format: dd-mm-yyyy
    time_str = current_datetime.strftime("%H:%M:%S")  # Format: hh:mm:ss
    result = type + '#' + date_str.replace('-', '') + time_str.replace(':', '')
    return result


def get_current_date():
    return datetime.now().strftime("%x")
