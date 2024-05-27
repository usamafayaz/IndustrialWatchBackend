from datetime import datetime


def get_formatted_number(type):
    current_datetime = datetime.now()
    date_str = current_datetime.strftime("%d-%m-%Y")  # Format: dd-mm-yyyy
    time_str = current_datetime.strftime("%H:%M:%S")  # Format: hh:mm:ss
    result = str(type) + '#' + date_str.replace('-', '') + time_str.replace(':', '')
    return result


def get_formatted_number_without_hash():
    current_datetime = datetime.now()
    date_str = current_datetime.strftime("%d-%m-%Y")  # Format: dd-mm-yyyy
    time_str = current_datetime.strftime("%H:%M:%S")  # Format: hh:mm:ss
    result = date_str.replace('-', '') + time_str.replace(':', '')
    return result


def get_current_date():
    return datetime.now().strftime("%x")


def get_first_three_characters(value):
    if len(value) >= 3:
        return value[0:3]


def convert_to_kg(weight, unit):
    if unit == 'g' or unit == 'G':
        return weight / 1000
    elif unit == 'mg' or unit == 'MG' or unit == 'Mg':
        return weight / 1000000
    else:
        return weight
