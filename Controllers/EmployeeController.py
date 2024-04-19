import DBHandler
from Models.Employee import Employee
from Models.User import User

def insert_employee(data, file_name):
    with DBHandler.return_session() as session:
        try:
            employee = Employee(name=data.get('name'), salary=data.get('salary'), job_role=data.get('jobRole'),
                                job_type=data.get('jobType'), date_joining=data.get('dateOfJoining'),
                                gender=data.get('gender'),
                                image=file_name, user_id=data.get('userId'))
            session.add(employee)
            session.commit()
            result = insert_employee_into_section(employee.id, data.get('sectionId'))
            if result:
                return {'message': 'Employee Inserted Successfully'}
            else:
                return {'message': 'Error Try again'}



        except Exception as e:
            return {'message': 'Error Try Again'}

