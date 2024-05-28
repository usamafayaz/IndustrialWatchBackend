import os
import queue
import threading
import time
from datetime import datetime, timedelta
import calendar

import cv2 as cv
from flask import jsonify
from sqlalchemy import func,extract
from ultralytics import YOLO

import DBHandler
import Util
from Models.Attendance import Attendance
from Models.Employee import Employee
from Models.EmployeeProductivity import EmployeeProductivity
from Models.EmployeeSection import EmployeeSection
from Models.ProductivityRule import ProductivityRule
from Models.Section import Section
from Models.SectionRule import SectionRule
from Models.Violation import Violation
from Models.ViolationImages import ViolationImages
from detection_models.facenet_predict import FaceRecognition
from trained_models import sitting_model

timeIntervals = {
    "start_time": None,
    "end_time": None
}

result_queue = queue.Queue()


def detect_employee_violation(file_path):
    employee = is_industry_employee(file_path)
    if employee is None:
        return jsonify({'message': 'Employee Not Found'}), 404
    else:
        threads = []
        for rule in employee['section_rules']:
            if rule['rule_id'] == 1:
                print('Start Mobile detection')
                t = threading.Thread(target=apply_detection_model, args=(
                    file_path,
                    f'D:\BSCS\Final Year Project\IndustrialWatchFYPBackend\\trained_models\mobile_detection.pt',
                    employee['employee_id'], 67, 1, rule['allowed_time'], result_queue))
                threads.append(t)
            elif rule['rule_id'] == 2:
                print('Start Smoke detection')
                t = threading.Thread(target=apply_detection_model, args=(
                    file_path,
                    f'D:\BSCS\Final Year Project\IndustrialWatchFYPBackend\\trained_models\cigarette_model.pt',
                    employee['employee_id'], 0, 2, rule['allowed_time'], result_queue))
                threads.append(t)
            elif rule['rule_id'] == 3:
                print('Start Sitting detection')
                t = threading.Thread(target=sitting_detection,
                                     args=(file_path, employee['employee_id'], 3, rule['allowed_time'], result_queue))
                threads.append(t)

        # Start all threads
        for t in threads:
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()
        results = []
        while not result_queue.empty():
            results.append(result_queue.get())

        # Process the results
        serialized_result = []
        for rule_id, result in results:

            if rule_id == 1:
                rule_name = 'Mobile Usage'
            elif rule_id == 2:
                rule_name = 'Smoking'
            else:
                rule_name = 'Sitting'
            serialized_result.append({'rule_name':rule_name,'total_time':result})
        calculate_productivity(employee['employee_id'])
        return jsonify(serialized_result), 200


def predict_with_model(img, model):
    results = model.predict(img, classes=[0, 67], save=True, imgsz=640, show_boxes=True, show_labels=True, show=True)
    class_id = None
    for result in results:
        boxes = result.boxes
        print(boxes)
        for box in boxes:
            class_id = int(box.cls)
        img_with_boxes = result.plot()
    return img_with_boxes, class_id


def apply_detection_model(video_path, model_path, employee_id, detection_class_id, rule_id, allowed_time, result_queue):
    model = YOLO(model_path)
    handle = cv.VideoCapture(video_path)
    violation_image_path = f'ViolationImages/{employee_id}'
    if not os.path.exists(violation_image_path):
        os.makedirs(violation_image_path)
    total_frames = int(handle.get(cv.CAP_PROP_FRAME_COUNT))
    fps = int(handle.get(cv.CAP_PROP_FPS))
    frame_interval = fps // 5  # 5 is desired frame
    frame_count = 0
    print(f"FPS of the video: {fps}")
    total_time = 0
    is_start = False
    violation_occurence = 0
    violationsCaptureWithImage = []
    for i in range(0, total_frames, frame_interval):
        handle.set(cv.CAP_PROP_POS_FRAMES, i)
        ret, frame = handle.read()

        if not ret:
            break

        if violation_occurence != 3:
            img_with_boxes, class_id = predict_with_model(frame, model)
            print(f"Predicting Frame Number: {i}")

            if class_id != None:
                if class_id == detection_class_id:  # Start Time
                    if not is_start:
                        timeIntervals["start_time"] = datetime.now().strftime('%H:%M:%S')
                        is_start = True
                    violation_occurence += 1
                    violationsCaptureWithImage.append(
                        {'capture_time': datetime.now().strftime('%H:%M:%S'), 'image': img_with_boxes})
                    # cv.imwrite(f'Violation/{employee_id}/{rule_id}/{frame_count}.jpg', img_with_boxes)
                    # cv.imshow("Frame", img_with_boxes)
        if i % 30 == 0 and i != 0 and violation_occurence == 3:
            total_time += 1
            print(f'clss id {rule_id} total time is  {total_time}')
            violation_occurence = 0

        frame_count += 1
        print(f"Frame Count: {frame_count}")

    print(f'Total Time: {total_time} for violation {rule_id}')

    if timeIntervals["start_time"] is not None:
        start_time_dt = datetime.strptime(timeIntervals["start_time"], '%H:%M:%S')
        end_time_dt = start_time_dt + timedelta(seconds=total_time)
        timeIntervals["end_time"] = end_time_dt.strftime('%H:%M:%S')

    print(f'Time Interval = {timeIntervals}')
    handle.release()

    print("Frames saved successfully.")
    violation_flag = get_violation(employee_id, rule_id)
    if violation_flag is not False:
        with DBHandler.return_session() as session:
            try:
                # updating existing violation time
                violation = session.query(Violation).filter(Violation.employee_id == employee_id).filter(
                    Violation.rule_id == rule_id).filter(Violation.date == datetime.now().strftime('%Y-%m-%d')).first()
                end_time = datetime.strptime(str(violation.end_time), '%H:%M:%S')
                print("Before Adding this Violation", violation.end_time)
                violation.end_time = str((end_time + timedelta(seconds=total_time)).strftime('%H:%M:%S'))
                print("After Adding this Violation", violation.end_time)
                add_violation_images(violation_image_path, violationsCaptureWithImage, violation.id, employee_id,
                                     violation.rule_id)
                session.commit()
            except Exception as e:
                print(f'Exception Occured, {str(e)}')
    elif violation_flag is False:
        # adding new violation
        with DBHandler.return_session() as session:
            try:
                violation_obj = Violation(employee_id=employee_id, rule_id=rule_id,
                                          date=datetime.now().strftime('%Y-%m-%d'),
                                          start_time=timeIntervals["start_time"], end_time=timeIntervals["end_time"])
                session.add(violation_obj)
                session.commit()
                new_violation = session.query(Violation).filter(Violation.employee_id == employee_id) \
                    .filter(Violation.rule_id == rule_id) \
                    .filter(Violation.date == violation_obj.date).first()
                if new_violation is not None:
                    add_violation_images(violation_image_path, violationsCaptureWithImage, new_violation.id,
                                         employee_id,
                                         rule_id)
            except Exception as e:
                print(f'Exception occurred, {str(e)}')
    result = total_time  # whatever your function returns
    result_queue.put((rule_id, result))

def calculate_productivity(employee_id):
    try:
        with DBHandler.return_session() as session:
            now = datetime.now()
            current_year = now.year
            current_month = now.month
            cal = calendar.monthcalendar(current_year, current_month)
            _, num_days = calendar.monthrange(current_year, current_month)

            total_fine = 0
            max_fine = 0
            days_without_weekend = 0
            for week in cal:
                # Filter out Saturday (5) and Sunday (6)
                for day_index in range(0, 5):  # Monday to Friday
                    if week[day_index] != 0:
                        days_without_weekend = days_without_weekend + 1
            total_working_days = session.query(func.count(Attendance.id)).filter(
                func.year(Attendance.attendance_date) == current_year,
                func.month(Attendance.attendance_date) == current_month,
                Attendance.employee_id == employee_id
            ).scalar()
            # Fetch the total fine and violation count
            result = session.query(Violation.start_time, Violation.end_time, Violation.date, SectionRule.allowed_time,
                                   SectionRule.fine) \
                .join(Employee, Violation.employee_id == Employee.id) \
                .join(EmployeeSection, Employee.id == EmployeeSection.employee_id) \
                .join(Section, EmployeeSection.section_id == Section.id) \
                .join(SectionRule, (Section.id == SectionRule.section_id) & (Violation.rule_id == SectionRule.rule_id)) \
                .filter(EmployeeSection.employee_id == employee_id) \
                .filter(extract('year', Violation.date) == current_year) \
                .filter(extract('month', Violation.date) == current_month) \
                .all()
            print(f'result-->> {result}')
            if result:
                for row in result:
                    start_time = datetime.strptime(str(row.start_time), "%H:%M:%S")
                    end_time = datetime.strptime(str(row.end_time), "%H:%M:%S") if row.end_time else None
                    allowed_time = datetime.strptime(str(row.allowed_time), "%H:%M:%S")
                    duration = end_time - start_time
                    allowed_duration = timedelta(hours=allowed_time.hour, minutes=allowed_time.minute,
                                                 seconds=allowed_time.second)

                    temp = ((days_without_weekend * 8) - round(
                        ((allowed_duration.total_seconds() / 3600) * days_without_weekend), 4)) * row.fine
                    max_fine = max_fine + temp
                    print(f'max fine -->> {max_fine} and temp fine -->>{temp}')
                    # condition to check duration and allowed time
                    if duration > allowed_duration:
                        fine = ((duration - allowed_duration).total_seconds()) * (
                                row.fine / allowed_duration.total_seconds())
                        total_fine = total_fine + fine
                print(f' {days_without_weekend}attendance -->> {(total_working_days / days_without_weekend) * 100}')
                print(f'halwa -->> {total_fine / total_working_days}')
                total_attendance = f"{total_working_days}/{num_days}"
                calculated_productivity = (((total_fine / max_fine) * 100) + ((total_working_days / num_days) * 100) / 2)
                productivity_from_db = session.query(EmployeeProductivity).filter(EmployeeProductivity.employee_id == employee_id) \
                    .filter(extract('month', EmployeeProductivity.productivity_month) == current_month) \
                    .first()
                # if not productivity_from_db and  productivity_from_db.productivity!=0 :
                productivity_from_db.productivity = productivity_from_db.productivity - round(calculated_productivity, 3)
                session.commit()
    except Exception as e:
        return None
def get_violation(employee_id, rule_id):
    with DBHandler.return_session() as session:
        try:
            violation = session.query(Violation).filter(Violation.employee_id == employee_id).filter(
                Violation.rule_id == rule_id).filter(Violation.date == datetime.now().strftime('%Y-%m-%d')).first()
            if violation:
                return True
            else:
                return False
        except Exception as e:
            print(f'Exception Occurred, {str(e)}')
            return None


def sitting_detection(video_path, employee_id, rule_id, allowed_time, result_queue):
    handle = cv.VideoCapture(video_path)
    violation_image_path = f'ViolationImages/{employee_id}'
    if not os.path.exists(violation_image_path):
        os.makedirs(violation_image_path)
    total_frames = int(handle.get(cv.CAP_PROP_FRAME_COUNT))
    fps = int(handle.get(cv.CAP_PROP_FPS))
    frame_interval = fps // 5  # 5 is desired frame
    frame_count = 0
    print(f"FPS of the video: {fps}")
    total_time = 0
    is_start = False
    violation_occurence = 0
    violationsCaptureWithImage = []
    for i in range(0, total_frames, frame_interval):
        handle.set(cv.CAP_PROP_POS_FRAMES, i)
        ret, frame = handle.read()

        if not ret:
            break

        if violation_occurence != 3:
            isSitting = sitting_model.sitting_detection_(frame)
            if isSitting:
                if not is_start:
                    timeIntervals["start_time"] = datetime.now().strftime('%H:%M:%S')
                    is_start = True
                violation_occurence += 1
                violationsCaptureWithImage.append(
                    {'capture_time': datetime.now().strftime('%H:%M:%S'), 'image': frame})
                # cv.imwrite(f'Violation/{employee_id}/{rule_id}/{frame_count}.jpg', img_with_boxes)
                # cv.imshow("Frame", img_with_boxes)

        if i % 30 == 0 and i != 0 and violation_occurence == 3:
            total_time += 1
            print(f'clss id {rule_id} total time is  {total_time}')
            violation_occurence = 0

        frame_count += 1
        print(f"Frame Count: {frame_count}")

    print(f'Total Time: {total_time} for violation {rule_id}')

    if timeIntervals["start_time"] is not None:
        start_time_dt = datetime.strptime(timeIntervals["start_time"], '%H:%M:%S')
        end_time_dt = start_time_dt + timedelta(seconds=total_time)
        timeIntervals["end_time"] = end_time_dt.strftime('%H:%M:%S')

    print(f'Time Interval = {timeIntervals}')
    handle.release()

    print("Frames saved successfully.")
    violation_flag = get_violation(employee_id, rule_id)
    if violation_flag is not False:
        with DBHandler.return_session() as session:
            try:
                # updating existing violation time
                violation = session.query(Violation).filter(Violation.employee_id == employee_id).filter(
                    Violation.rule_id == rule_id).filter(Violation.date == datetime.now().strftime('%Y-%m-%d')).first()
                end_time = datetime.strptime(str(violation.end_time), '%H:%M:%S')
                print("Before Adding this Violation", violation.end_time)
                violation.end_time = str((end_time + timedelta(seconds=total_time)).strftime('%H:%M:%S'))
                print("After Adding this Violation", violation.end_time)
                add_violation_images(violation_image_path, violationsCaptureWithImage, violation.id, employee_id,
                                     rule_id)
                session.commit()
            except Exception as e:
                print(f'Exception Occurred, {str(e)}')
    elif violation_flag is False:
        # adding new violation
        with DBHandler.return_session() as session:
            try:
                violation_obj = Violation(employee_id=employee_id, rule_id=rule_id,
                                          date=datetime.now().strftime('%Y-%m-%d'),
                                          start_time=timeIntervals["start_time"], end_time=timeIntervals["end_time"])
                session.add(violation_obj)

                session.commit()
                new_violation = session.query(Violation).filter(Violation.employee_id == employee_id) \
                    .filter(Violation.rule_id == rule_id) \
                    .filter(Violation.date == violation_obj.date).first()
                if new_violation is not None:
                    add_violation_images(violation_image_path, violationsCaptureWithImage, new_violation.id,
                                         employee_id,
                                         rule_id)
            except Exception as e:
                print(f'Exception occurred, {str(e)}')
    result = total_time  # whatever your function returns
    result_queue.put((rule_id, result))


def is_industry_employee(file_path):
    image = extract_frame_from(file_path)
    if image is not None:
        facerecoganizer = FaceRecognition()
        person = facerecoganizer.predict(image)
        print("dsadsad", person)
        if person is not None and person != 'No face detected':
            print(f'Prediction = {person[0]}')
            section_id = get_employee_section_id(int(person[0]))
            print(f'Prediction = {section_id}')
            section_detail = get_section_detail(section_id)
            employee = {
                'employee_id': int(person[0]),
                'section_rules': []
            }
            for rule in section_detail['rules']:
                obj = {
                    'rule_id': rule['rule_id'],
                    'fine': rule['fine'],
                    'allowed_time': rule['allowed_time']
                }
                employee['section_rules'].append(obj)
            return employee
        else:
            return None
    else:
        return None


def extract_frame_from(video_path):
    try:
        cam = cv.VideoCapture(video_path)
        if not cam.isOpened():
            return None

        ret, frame = cam.read()
        if ret:
            # output_folder = 'EmployeeImages'
            # frame_path = os.path.join('EmployeeImages', f'akhroot.jpg')
            # cv.imwrite(frame_path, frame)
            return frame
        else:
            return None
    except Exception as e:
        print(f"Error extracting frame: {e}")
        return None
    finally:
        cam.release()


def get_section_detail(id):
    with DBHandler.return_session() as session:
        try:
            section = session.query(Section).filter(Section.id == id).first()
            if section == None:
                print(jsonify({'message': 'Section not found'}), 500)
            print(f'Section a gya Sai')
            query = session.query(Section, SectionRule, ProductivityRule).join(SectionRule,
                                                                               Section.id == SectionRule.section_id).join(
                ProductivityRule, SectionRule.rule_id == ProductivityRule.id).filter(Section.id == id)
            result = query.all()
            data = {
                'id': section.id,
                'name': section.name,
                'rules': []
            }
            for sec, section_rule, productivity_rule in result:
                data['rules'].append({
                    'rule_id': productivity_rule.id,
                    'rule_name': productivity_rule.name,
                    'allowed_time': str(section_rule.allowed_time),
                    'fine': section_rule.fine
                })
            return data
        except Exception as e:
            print(jsonify({'message': str(e)}), 500)
            return None


def get_employee_section_id(employee_id):
    with DBHandler.return_session() as session:
        try:
            section = session.query(EmployeeSection).filter(EmployeeSection.employee_id == employee_id).first()
            return section.section_id
        except Exception as e:
            return None


def mark_attendance(video_path):
    try:
        with DBHandler.return_session() as session:
            employee = is_industry_employee(video_path)
            if employee is None:
                print(f'employee none hai')

                return jsonify({'message': 'Employee Not Found'}), 404
            else:
                attendance = session.query(Attendance).filter(Attendance.employee_id == employee['employee_id']).first()
                if attendance is not None:
                    print(f'attendance --->> {attendance.attendance_date}')
                    attendance.check_out = datetime.now().strftime('%H:%M:%S')
                    session.commit()
                    return False
                else:
                    session.add(Attendance(
                        check_in=datetime.now().strftime('%H:%M:%S'),
                        attendance_date=Util.get_current_date(),
                        employee_id=employee['employee_id']
                    ))
                    session.commit()
                    return True
    except Exception as e:
        print(f'attendance excep-->> {str(e)}')
        return None


def add_violation_images(path, captured_violations, violation_id, employee_id, rule_id):
    try:
        with DBHandler.return_session() as session:
            for i in captured_violations:
                time.sleep(1)
                image_name = Util.get_formatted_number_without_hash()
                # path=f'ViolationImages/{employee_id}/{rule_id}'
                # if not os.path.exists(path):
                #     os.makedirs(path)
                print(f'path-->>{path}')
                print(f'rule id -->> {rule_id} and Violation id {violation_id} and Employee id {employee_id}')
                if not os.path.exists(f'ViolationImages/{employee_id}/{rule_id}'):
                    os.makedirs(f'ViolationImages/{employee_id}/{rule_id}')
                image_path = os.path.join(f'ViolationImages/{employee_id}/{rule_id}', f'{image_name}.jpg')
                cv.imwrite(image_path, i.get('image'))
                image_path = os.path.join(f'{employee_id}/{rule_id}', f'{image_name}.jpg')
                violation_with_image = ViolationImages(violation_id=violation_id, image_url=image_path,
                                                       capture_time=i.get('capture_time'))
                session.add(violation_with_image)
            session.commit()
            return True
    except Exception as e:
        print(f'excep -->> {str(e)}')
        return False
