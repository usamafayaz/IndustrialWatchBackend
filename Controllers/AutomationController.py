import  cv2 as cv
import os
from detection_models.facenet_predict import FaceRecognition
from Controllers import  SectionController
from flask import jsonify
from Models.EmployeeSection import EmployeeSection
from Models.Section import Section
from Models.SectionRule import SectionRule
from Models.ProductivityRule import ProductivityRule
import DBHandler
from flask import jsonify


def detect_employee_violation(file):
    employee = is_industry_employee(file)
    if employee is None:
        return jsonify({'meassage' : 'Employee Not Found'}), 404
    else:
        for rule in employee['section_rules']:
            if rule['rule_id'] == 1:
                mobile_detection()
            elif rule['rule_id'] == 2:
                smoking_detection()
            elif rule['rule_id'] == 3:
                sitting_detection()
        return jsonify({'meassage' : 'Employee Found'}), 200


def mobile_detection():
    pass
def smoking_detection():
    pass
def sitting_detection():
    pass


def is_industry_employee(file):
    image = extract_frame_from(file)
    if image is not None:
        facerecoganizer = FaceRecognition()
        person = facerecoganizer.predict(image)

        if person is not None and person != 'No face detected':
            print(f'Prediction = {person[0]}')
            section_id = get_employee_section_id(int(person[0]))
            print(f'Prediction = {section_id}')
            section_detail = get_section_detail(section_id)
            employee = {
                'employee_id' : int(person[0]),
                'section_rules' : []
            }
            for rule in section_detail['rules']:
                obj = {
                    'rule_id' : rule['rule_id'],
                    'fine' : rule['fine'],
                    'allowed_time' : rule['allowed_time']
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
                print( jsonify({'message': 'Section not found'}), 500)
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
