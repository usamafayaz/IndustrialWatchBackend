import calendar
import os
import time
from datetime import date, datetime

from flask import jsonify
from sqlalchemy import func, extract

import DBHandler
import Util
from Models.Attendance import Attendance
from Models.Employee import Employee
from Models.EmployeeImages import EmployeeImages
from Models.EmployeeProductivity import EmployeeProductivity
from Models.EmployeeSection import EmployeeSection
from Models.JobRole import JobRole
from Models.ProductivityRule import ProductivityRule
from Models.Section import Section
from Models.SectionRule import SectionRule
from Models.User import User
from Models.Violation import Violation
from Models.ViolationImages import ViolationImages
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
            user_role = ''
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
            productivity = EmployeeProductivity(employee_id=employee.id, productivity=100,
                                                productivity_month=datetime.today().strftime('%Y-%m-%d'))
            session.add(productivity)
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
            return False


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


def get_all_supervisors():
    with DBHandler.return_session() as session:
        try:
            supervisors = session.query(Employee.name, Section.name, Employee.id). \
                join(EmployeeSection, Employee.id == EmployeeSection.employee_id). \
                join(Section, Section.id == EmployeeSection.section_id). \
                join(User, User.id == Employee.user_id). \
                filter(User.user_role == 'Supervisor').all()
            if supervisors:
                supervisors_dict = {}
                for supervisor in supervisors:
                    employee_id = supervisor.id
                    employee_name = supervisor[0]
                    section_name = supervisor[1]
                    if employee_id not in supervisors_dict:
                        supervisors_dict[employee_id] = {
                            'employee_id': employee_id,
                            'employee_name': employee_name,
                            'sections': [section_name]
                        }
                    else:
                        supervisors_dict[employee_id]['sections'].append(section_name)

                supervisors_list = list(supervisors_dict.values())
                return jsonify(supervisors_list), 200
            else:
                return jsonify({'message': 'No Data Found'}), 500
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def get_supervisor_detail(supervisor_id):
    with DBHandler.return_session() as session:
        try:
            supervisor_detail = session.query(User.username, User.password, Section.name, Section.id) \
                .join(Employee, User.id == Employee.user_id) \
                .join(EmployeeSection, Employee.id == EmployeeSection.employee_id) \
                .join(Section, Section.id == EmployeeSection.section_id) \
                .filter(Employee.id == supervisor_id) \
                .all()

            if supervisor_detail:
                user_data = {}
                for user, password, section_name, section_id in supervisor_detail:
                    if user not in user_data:
                        user_data[user] = {'password': password, 'sections': []}
                    user_data[user]['sections'].append({'name': section_name, 'id': section_id})

                result = [{'username': user, 'password': data['password'], 'sections': data['sections']} for user, data
                          in user_data.items()]

                return jsonify(result), 200
            else:
                return jsonify({'message': 'No Data Found'}), 500
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def update_supervisor(data):
    with DBHandler.return_session() as session:
        try:
            supervisor = session.query(User).join(Employee, User.id == Employee.user_id).filter(
                Employee.id == data.get('employee_id')).first()
            if supervisor:
                # Fetch all EmployeeSection objects related to the supervisor
                employee_sections = session.query(EmployeeSection).filter(
                    EmployeeSection.employee_id == data.get('employee_id')).all()

                # Delete all fetched EmployeeSection objects
                for employee_section in employee_sections:
                    session.delete(employee_section)

                # Update supervisor's username and password
                supervisor.username = data.get('username')
                supervisor.password = data.get('password')

                # Add new sections
                sections = data.get('sections')
                for section in sections:
                    session.add(
                        EmployeeSection(employee_id=data.get('employee_id'), section_id=section,
                                        date_time=Util.get_current_date()))

                session.commit()

                return jsonify({'message': 'Supervisor Updated'}), 200
            else:
                return jsonify({'message': 'Supervisor not found'}), 404
        except Exception as e:
            session.rollback()
            return jsonify({'message': str(e)}), 500


def get_all_employees(section_id, ranking_required):
    with DBHandler.return_session() as session:
        try:
            if int(ranking_required) == 0:
                if int(section_id) == -1:
                    employees = session.query(Employee.id, Employee.name, Section.name, JobRole.name,
                                              EmployeeProductivity.productivity) \
                        .join(EmployeeSection, Employee.id == EmployeeSection.employee_id) \
                        .join(EmployeeProductivity, EmployeeProductivity.employee_id == Employee.id) \
                        .join(Section, EmployeeSection.section_id == Section.id) \
                        .join(JobRole, Employee.job_role_id == JobRole.id) \
                        .all()
                else:
                    employees = session.query(Employee.id, Employee.name, Section.name, JobRole.name,
                                              EmployeeProductivity.productivity) \
                        .join(EmployeeSection, Employee.id == EmployeeSection.employee_id) \
                        .join(EmployeeProductivity, EmployeeProductivity.employee_id == Employee.id) \
                        .join(Section, EmployeeSection.section_id == Section.id) \
                        .join(JobRole, Employee.job_role_id == JobRole.id) \
                        .filter(EmployeeSection.section_id == section_id) \
                        .all()
            else:
                current_date = datetime.now()
                if int(section_id) == -1:
                    employees = session.query(Employee.id, Employee.name, Section.name, JobRole.name,
                                              EmployeeProductivity.productivity) \
                        .join(EmployeeSection, Employee.id == EmployeeSection.employee_id) \
                        .join(EmployeeProductivity, EmployeeProductivity.employee_id == Employee.id) \
                        .join(Section, EmployeeSection.section_id == Section.id) \
                        .join(JobRole, Employee.job_role_id == JobRole.id) \
                        .order_by(EmployeeProductivity.productivity.desc()) \
                        .all()
                else:
                    employees = session.query(Employee.id, Employee.name, Section.name, JobRole.name,
                                              EmployeeProductivity.productivity) \
                        .join(EmployeeSection, Employee.id == EmployeeSection.employee_id) \
                        .join(EmployeeProductivity, EmployeeProductivity.employee_id == Employee.id) \
                        .join(Section, EmployeeSection.section_id == Section.id) \
                        .join(JobRole, Employee.job_role_id == JobRole.id) \
                        .filter(EmployeeSection.section_id == section_id) \
                        .order_by(EmployeeProductivity.productivity.desc()) \
                        .all()
            serialize = []
            if len(employees) == 0:
                return jsonify({'message': 'No Record Found'}), 404
            for employee in employees:
                images = session.query(EmployeeImages.image_url).filter(
                    EmployeeImages.employee_id == employee[0]).all()
                image_urls = [image[0] for image in images]
                serialize.append({
                    'employee_id': employee[0],
                    'name': employee[1],
                    'section_name': employee[2],
                    'job_role': employee[3],
                    'productivity': employee[4],
                    'image': image_urls[0]
                })
            return jsonify(serialize), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def get_employee_detail(employee_id):
    try:
        with DBHandler.return_session() as session:
            total_fine = session.query(func.sum(SectionRule.fine)) \
                .join(EmployeeSection, EmployeeSection.section_id == SectionRule.section_id) \
                .join(Violation, (Violation.rule_id == SectionRule.rule_id) & (
                    Violation.employee_id == EmployeeSection.employee_id)) \
                .filter(Violation.employee_id == employee_id) \
                .scalar()
            productivity = session.query(EmployeeProductivity.productivity).filter(
                EmployeeProductivity.employee_id == employee_id).scalar()
            if total_fine is None:
                total_fine = 0
        return jsonify({'total_fine': total_fine, 'productivity': productivity})
    except Exception as e:
        return jsonify({'message': str(e)}), 500


def get_employee_attendance(employee_id):
    with DBHandler.return_session() as session:
        try:
            # Get all attendance records for the employee
            attendance = session.query(Attendance).filter(Attendance.employee_id == int(employee_id)).all()

            if len(attendance) == 0:
                return jsonify({'message': 'Record not found.'}), 500

            # Create a dictionary to store attendance by date
            attendance_dict = {att.attendance_date.strftime("%Y-%m-%d"): att for att in attendance}

            # Get current year and month
            today = date.today()
            current_year = today.year
            current_month = today.month
            current_day = today.day

            # Get the total number of days in the current month
            _, num_days = calendar.monthrange(current_year, current_month)

            # Initialize a list to store serialized attendance
            serialize_attendance = []

            # Iterate through each day of the month up to today's date
            for day in range(1, current_day + 1):
                # Construct the date
                attendance_date = datetime(current_year, current_month, day).strftime("%Y-%m-%d")

                # Check if the day is a weekday (Monday to Friday)
                if datetime.strptime(attendance_date, "%Y-%m-%d").weekday() < 5:
                    # If the attendance record exists for the date, serialize it
                    if attendance_date in attendance_dict:
                        serialize_attendance.append({'attendance_date': attendance_date, 'status': 'P'})
                    # If the attendance record doesn't exist, mark as 'A'
                    else:
                        serialize_attendance.append({'attendance_date': attendance_date, 'status': 'A'})

            return jsonify(serialize_attendance), 200


        except Exception as e:
            return jsonify({'message': str(e)}), 500


def mark_attendance(employee_id):
    with DBHandler.return_session() as session:
        try:
            today = date.today()
            current_year = today.year
            current_month = today.month
            cal = calendar.monthcalendar(current_year, current_month)
            weekday_dates = []

            # Iterate through each week
            for week in cal:
                # Filter out Saturday (5) and Sunday (6)
                for day_index in range(0, 5):  # Monday to Friday
                    if week[day_index] != 0:
                        # Append the date to the list
                        # weekday_dates.append()
                        session.add(Attendance(
                            check_in='08:00',
                            check_out='17:00',
                            attendance_date=date(current_year, current_month, week[day_index]),
                            employee_id=employee_id
                        ))
            session.commit()
            return jsonify({'message': 'Attendance Marked'}), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500


# def add_violation():
#     pass
#

def get_employee_violations(employee_id):
    with DBHandler.return_session() as session:
        try:
            violations = session.query(Violation, ProductivityRule.name.label("rule_name")) \
                .join(ProductivityRule, Violation.rule_id == ProductivityRule.id) \
                .filter(Violation.employee_id == employee_id) \
                .all()
            serialized_violations = []
            for violation, rule_name in violations:
                images = get_violation_images(violation.id)
                obj = {
                    "violation_id": violation.id,
                    "date": violation.date.strftime("%d-%m-%Y"),
                    "time": violation.start_time.strftime("%H:%M"),
                    "rule_name": rule_name,
                    "images": images
                }
                serialized_violations.append(obj)
            return jsonify(serialized_violations), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def get_violation_images(violation_id):
    with DBHandler.return_session() as session:
        try:
            violation_images = session.query(ViolationImages.image_url) \
                .join(Violation, Violation.id == ViolationImages.violation_id) \
                .join(Employee, Employee.id == Violation.employee_id) \
                .filter(ViolationImages.violation_id == violation_id) \
                .all()
            images = []
            for image in violation_images:
                images.append(image.image_url)
            return images
        except Exception as e:
            return []


def get_violation_details(violation_id):
    with DBHandler.return_session() as session:
        try:
            violation = session.query(
                Violation.id.label('violation_id'),
                Violation.date,
                Violation.start_time.label('time'),
                ProductivityRule.name.label('rule_name'),
                Section.name.label('section_name')
            ).select_from(Violation) \
                .join(ProductivityRule, Violation.rule_id == ProductivityRule.id) \
                .join(EmployeeSection, Violation.employee_id == EmployeeSection.employee_id) \
                .join(Section, EmployeeSection.section_id == Section.id) \
                .filter(Violation.id == violation_id) \
                .first()
            if violation is None:
                return jsonify({"message": "Violation not found"}), 404
            images = get_violation_images(violation_id)
            serialized_violation = {
                "violation_id": violation.violation_id,
                "date": violation.date,
                "time": str(violation.time),
                "rule_name": violation.rule_name,
                "section_name": violation.section_name,
                "images": images
            }
            return jsonify(serialized_violation), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def get_employee_summary(employee_id, date):
    with DBHandler.return_session() as session:
        try:
            # Parse the month and year from the date string
            month, year = map(int, date.split(','))

            total_fine = 0
            violation_count = 0

            # Fetch the total fine and violation count
            result = session.query(
                func.sum(SectionRule.fine),
                func.count(Violation.id)
            ) \
            .join(EmployeeSection, EmployeeSection.section_id == SectionRule.section_id) \
            .join(Violation, (Violation.rule_id == SectionRule.rule_id) & (Violation.employee_id == EmployeeSection.employee_id)) \
            .filter(Violation.employee_id == employee_id) \
            .filter(extract('year', Violation.date) == year) \
            .filter(extract('month', Violation.date) == month) \
            .first()

            if result:
                total_fine = result[0] if result[0] is not None else 0
                violation_count = result[1]

            # Fetch attendance records
            attendance = session.query(Attendance).filter(
                Attendance.employee_id == int(employee_id),
                extract('year', Attendance.attendance_date) == year,
                extract('month', Attendance.attendance_date) == month
            ).all()

            # Handle case where no attendance records are found
            if not attendance:
                attendance_rate = 'N/A'
            else:
                # Create a dictionary to store attendance by date
                attendance_dict = {att.attendance_date.strftime("%Y-%m-%d"): att for att in attendance}

                # Get the total number of days in the specified month
                _, num_days = calendar.monthrange(year, month)

                # Initialize counters
                total_days = 0
                present_days = 0

                # Iterate through each day of the month
                for day in range(1, num_days + 1):
                    attendance_date = datetime(year, month, day).strftime("%Y-%m-%d")
                    current_date = datetime.strptime(attendance_date, "%Y-%m-%d")

                    # Check if the day is a weekday (Monday to Friday)
                    if current_date.weekday() < 5:
                        total_days += 1
                        # If the attendance record exists for the date, mark as present
                        if attendance_date in attendance_dict:
                            present_days += 1

                attendance_rate = f"{present_days}/{num_days}"

            # Serialize the summary
            serialize_summary = {
                "total_fine": total_fine,
                "violation_count": violation_count,
                "attendance_rate": attendance_rate
            }

            return jsonify(serialize_summary), 200

        except Exception as e:
            return jsonify({'message': str(e)}), 500

def get_employee_profile(employee_id):
    try:
        with DBHandler.return_session() as session:
            employee_details = session.query(Employee.name, Employee.job_type, JobRole.name.label('job_role_name'),
                                             Section.name.label('section_name'), User.username, User.password,
                                             EmployeeImages.image_url) \
                .join(JobRole, Employee.job_role_id == JobRole.id) \
                .join(EmployeeSection, Employee.id == EmployeeSection.employee_id) \
                .join(Section, EmployeeSection.section_id == Section.id) \
                .join(User, User.id == Employee.user_id) \
                .join(EmployeeImages, EmployeeImages.employee_id == Employee.id) \
                .filter(Employee.id == employee_id).first()
            if employee_details:
                return jsonify({
                    'name': employee_details[0],
                    'job_type': employee_details[1],
                    'job_role': employee_details[2],
                    'section': employee_details[3],
                    'username': employee_details[4],
                    'password': employee_details[5],
                    'image': employee_details[6],
                })
            else:
                return jsonify({'message': 'Employee not found'}), 404
    except Exception as e:
        return jsonify({'message': str(e)}), 500


def update_employee_profile(data):
    with DBHandler.return_session() as session:
        try:
            employee = session.query(Employee).filter(Employee.id == data['id']).first()
            user = session.query(User).join(Employee, Employee.user_id == User.id).filter(
                Employee.id == data['id']).first()
            if employee and user:
                employee.name = data['name']
                user.username = data['username']
                user.password = data['password']
                session.commit()
                return jsonify({'message': 'Information Updated'}), 200
            else:
                return jsonify({'message': 'An Error Occured'}), 404
        except Exception as e:
            return jsonify({'message': str(e)}), 500