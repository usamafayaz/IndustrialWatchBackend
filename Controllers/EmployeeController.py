import os, time
from flask import jsonify
import DBHandler
import Util
from Models.Employee import Employee
from Models.EmployeeSection import EmployeeSection
from Models.JobRole import JobRole
from Models.EmployeeImages import EmployeeImages
from Models.User import User
from route import app

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def login(username, password):
    try:
        session = DBHandler.return_session()
        user = session.query(User).filter(User.username == username, User.password == password).first()

        if user:
            employee = session.query(Employee).filter(Employee.user_id == user.id).first()
            user_data = {
                'id': employee.id,
                'name': employee.name,
                'user_role': user.user_role
            }
            return jsonify(user_data), 200
        else:
            return jsonify({"message": "User not found or incorrect credentials"}), 500
    except Exception as e:
        return jsonify({'message': str(e)}), 500


def add_employee(data):
    with DBHandler.return_session() as session:
        try:
            job_role = session.query(JobRole).filter(JobRole.id == data.get('job_role_id')).first()
            if job_role.name == 'Supervisor' or job_role.name == 'supervisor':
                user_role = 'Supervisor'
            else:
                user_role = 'Employee'
            user = add_user(data.get('username'), data.get('password'), user_role)
            if user is None:
                return jsonify({'message': 'Error in adding employee,Try again'}), 500
            employee = Employee(name=data.get('name'), salary=data.get('salary'),
                                job_role_id=data.get('job_role_id'),
                                job_type=data.get('job_type'), date_of_joining=Util.get_current_date(),
                                gender=data.get('gender'), user_id=user.id)
            session.add(employee)
            session.commit()
            is_images_saved = add_employee_images(employee.name, employee.id, data.get('images'))
            if is_images_saved is False:
                delete_user_and_employee(user, employee)
                return jsonify({'message': 'Error in adding employee,Try again'}), 500
            # employee_id = session.query(Employee.id).filter(Employee.id == user.id).first()
            is_employee_added_to_sec = add_employee_to_section(employee.id, section_id=data.get('section_id'))
            if is_employee_added_to_sec is False:
                delete_user_and_employee(user, employee)
                return jsonify({'message': 'Error in adding employee,Try again'}), 500
            return jsonify({'message': 'Employee Added Successfully'}), 200
        except Exception as e:
            delete_user_and_employee(user, employee)
            return jsonify({'message': str(e)}), 500


def add_user(username, password, user_role):
    with DBHandler.return_session() as session:
        try:
            user = User(username=username, password=password, user_role=user_role)
            session.add(user)
            session.commit()
            user = session.query(User).filter(User.username == username).filter(User.password == password).filter(
                User.user_role == user_role).first()
            return user
        except Exception as e:
            return None


def delete_user_and_employee(user, employee):
    with DBHandler.return_session() as session:
        try:
            session.delete(employee)
            session.delete(user)
            session.commit()
            return None
        except Exception as e:
            return e


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def add_employee_images(name, employee_id, images_list):
    with DBHandler.return_session() as session:
        try:
            if not os.path.exists('EmployeeImages'):
                os.makedirs('EmployeeImages')
            for image in images_list:
                if image and allowed_file(image.filename):
                    filename = Util.get_formatted_number(Util.get_first_three_characters(name)) + \
                               image.filename
                    image.save(os.path.join(app.config['EmployeeImages'], filename))
                    session.add(EmployeeImages(employee_id=employee_id, image_url=filename))
                    time.sleep(1)
                    session.commit()
            return True
        except Exception as e:
            False


def add_employee_to_section(employee_id, section_id, ):
    with DBHandler.return_session() as session:
        try:
            session.add(
                EmployeeSection(employee_id=employee_id, section_id=section_id,
                                date_time=Util.get_current_date()))
            session.commit()
            return True
        except Exception as e:
            return False


def get_all_job_roles():
    with DBHandler.return_session() as session:
        try:
            job_roles = session.query(JobRole).all()
            if job_roles:
                job_roles_data = []
                for job_role in job_roles:
                    data = {
                        'id': job_role.id,
                        'name': job_role.name,
                    }
                    job_roles_data.append(data)
                return jsonify(job_roles_data), 200
            else:
                return jsonify({'message': 'No Data Found'}), 500
        except Exception as e:
            return jsonify({'message': str(e)}), 500
