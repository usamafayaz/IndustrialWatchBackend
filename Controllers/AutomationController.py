import os
import threading
from datetime import datetime, timedelta

import cv2 as cv
from flask import jsonify
from ultralytics import YOLO

import DBHandler
from Models.EmployeeSection import EmployeeSection
from Models.ProductivityRule import ProductivityRule
from Models.Section import Section
from Models.SectionRule import SectionRule
from Models.Violation import Violation
from detection_models.facenet_predict import FaceRecognition

timeIntervals = {
    "start_time": None,
    "end_time": None
}


def detect_employee_violation(file_path):
    employee = is_industry_employee(file_path)
    if employee is None:
        return jsonify({'meassage': 'Employee Not Found'}), 404
    else:
        threads = []
        for rule in employee['section_rules']:
            if rule['rule_id'] == 1:
                print('Mobile detection Chalao')
                t = threading.Thread(target=apply_detection_model, args=(
                    file_path,
                    f'D:\BSCS\Final Year Project\IndustrialWatchFYPBackend\\trained_models\mobile_detection.pt',
                    employee['employee_id'], 67, 1, rule['allowed_time']))
                threads.append(t)
            elif rule['rule_id'] == 2:
                print('Smoke detection Chalao')
                t = threading.Thread(target=apply_detection_model, args=(
                    file_path,
                    f'D:\BSCS\Final Year Project\IndustrialWatchFYPBackend\\trained_models\cigarette_model.pt',
                    employee['employee_id'], 0, 2, rule['allowed_time']))
                threads.append(t)
            elif rule['rule_id'] == 3:
                print('Sitting detection Chalao')
                t = threading.Thread(target=sitting_detection)
                threads.append(t)

        # Start all threads
        for t in threads:
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()
        return jsonify({'meassage': 'Employee Found'}), 200


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


def apply_detection_model(video_path, model_path, employee_id, detection_class_id, rule_id, allowed_time):
    model = YOLO(model_path)
    handle = cv.VideoCapture(video_path)
    violation_image_path = f'Violation/{employee_id}/{rule_id}'
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
                    cv.imwrite(f'Violation/{employee_id}/{rule_id}/{frame_count}.jpg', img_with_boxes)
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
                violation = session.query(Violation).filter(Violation.employee_id == employee_id).filter(
                    Violation.rule_id == rule_id).filter(Violation.date == datetime.now().strftime('%Y-%m-%d')).first()
                end_time = datetime.strptime(str(violation.end_time), '%H:%M:%S')
                print("Before Adding this Violation", violation.end_time)
                violation.end_time = str((end_time + timedelta(seconds=total_time)).strftime('%H:%M:%S'))
                print("After Adding this Violation", violation.end_time)
                session.commit()
            except Exception as e:
                print(f'Exception Occured, {str(e)}')
    elif violation is False:
        with DBHandler.return_session() as session:
            try:
                violation_obj = Violation(employee_id=employee_id, rule_id=rule_id,
                                          date=datetime.now().strftime('%Y-%m-%d'),
                                          start_time=timeIntervals["start_time"], end_time=timeIntervals["end_time"])
                session.add(violation_obj)
                session.commit()

            except Exception as e:
                print(f'Exception Occured, {str(e)}')


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
            print(f'Exception Occured, {str(e)}')
            return None


def sitting_detection():
    pass


def is_industry_employee(file_path):
    image = extract_frame_from(file_path)
    if image is not None:
        facerecoganizer = FaceRecognition()
        person = facerecoganizer.predict(image)
        print("dsadsad", person)
        if person is not None and person != 'No face detected':
            print(f'Prediction = {person[0]}')
            section_id = get_employee_section_id(int(person[0]))
            # Add Attendance ~~~~
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
