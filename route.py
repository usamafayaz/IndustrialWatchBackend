import os

from flask import Flask, jsonify, request, send_from_directory

from controllers import UserController, RuleController, SupervisorController, SectionController, ProductController, \
    EmployeeController
from Models.Section import Section
from Models.Rule import ProductivityRule

app = Flask(__name__)
UPLOAD_FOLDER = 'EmployeeImages'
app.config['EmployeeImages'] = UPLOAD_FOLDER


@app.route('/api/User/InsertUser', methods=['POST'])
def insert_user():
    data = request.get_json()
    return UserController.insert_user(data)


@app.route('/api/User/GetAllUsers', methods=['GET'])
def get_all_user():
    return jsonify(UserController.get_all_user())


@app.route('/api/User/GetUser/', methods=['GET'])
def get_user():
    user_id = request.args.get('id')
    response = UserController.get_user(user_id=user_id)
    return jsonify(response)


@app.route('/api/User/UpdateUser', methods=['PUT'])
def update_user():
    data = request.get_json()
    response = UserController.update_user(data)
    return jsonify(response)


@app.route('/api/User/DeleteUser/', methods=['DELETE'])
def delete_user():
    user_id = request.args.get('id')
    print(user_id)
    response = UserController.delete_user(user_id)
    return jsonify(response)


@app.route('/api/User/Login', methods=['GET'])
def login():
    response = UserController.login(username=request.args.get('username'), password=request.args.get('password'))
    return response


#####################SupervisorController#####################
@app.route('/api/Supervisor/insert_supervisor', methods=['POST'])
def InsertSupervisor():
    data = request.get_json()
    response = SupervisorController.insert_supervisor(data)
    return response


@app.route('/api/Supervisor/GetAllSupervisors', methods=['GET'])
def GetAllSupervisors():
    serialize = SupervisorController.get_all_supervisors()
    return serialize


@app.route('/api/Supervisor/GetSupervisor/<int:supervisorID>', methods=['GET'])
def GetSupervisor(supervisorID):
    response = SupervisorController.GetSupervisor(supervisorID)
    return response


@app.route('/api/Supervisor/UpdateSupervisor', methods=['PUT'])
def UpdateSupervisor():
    jsondata = request.get_json()
    response = SupervisorController.update_supervisor(jsondata)
    return response


@app.route('/api/Supervisor/DeleteSupervisor/', methods=['DELETE'])
def DeleteSupervisor():
    response = SupervisorController.delete_supervisor(request.args.get('id'))
    return response

@app.route('/api/Supervisor/MoniterEmployees', methods=['POST'])
def MoniterEmployees():
    return jsonify('Ok'), 200


@app.route('/api/Supervisor/DefectMoniteringCamera1', methods=['POST'])
def DefectMoniteringCamera1():
    return jsonify('Ok'), 200


@app.route('/api/Supervisor/DefectMoniteringCamera2', methods=['POST'])
def DefectMoniteringCamera2():
    return jsonify('Ok'), 200


@app.route('/api/Supervisor/DefectMoniteringCamera3', methods=['POST'])
def DefectMoniteringCamera3():
    return jsonify('Ok'), 200


@app.route('/api/Supervisor/DefectMoniteringCamera4', methods=['POST'])
def DefectMoniteringCamera4():
    return jsonify('Ok'), 200


@app.route('/api/Supervisor/DefectMoniteringCamera5', methods=['POST'])
def DefectMoniteringCamera5():
    return jsonify('Ok'), 200


############################SectionController#############################
@app.route('/api/Section/InsertSection', methods=['POST'])
def insert_section():
    data = request.get_json()
    print(data)
    response = SectionController.insert_new_section_with_rule(data)
    return response




@app.route('/api/Section/GetAllSections', methods=['GET'])
def get_all_section():
    response = SectionController.get_all_sections()
    return response


@app.route('/api/Section/GetSection/', methods=['GET'])
def get_section():
    response = SectionController.get_section(request.args.get('id'))
    return jsonify(response)


@app.route('/api/Section/UpdateSection', methods=['PUT'])
def update_section():
    request_data = request.get_json()
    response = SectionController.update_section(request_data)
    return jsonify(response)


@app.route('/api/Section/DeleteSection/', methods=['DELETE'])
def delete_section():
    response = SectionController.delete_section(request.args.get('id'))
    return jsonify(response)


@app.route('/api/Section/InsertRulesToSection', methods=['POST'])
def insert_rules_to_section():
    data = request.get_json()
    print(data)
    response = SectionController.insert_new_section_with_rule(data)
    return response


@app.route('/api/Section/GetAllSectionWithRule', methods=['GET'])
def get_all_section_with_rule():
    response = SectionController.get_all_section_with_rule()
    return response


@app.route('/api/Section/GetRulesForSection/', methods=['GET'])
def get_rules_for_section():
    response = SectionController.get_rules_for_section(request.args.get('id'))
    return response


######## Rule Controller #########
@app.route('/api/Rule/AddRule', methods=['POST'])
def insert_rule():
    response = RuleController.insert_rule(request.args.get('name'))
    return jsonify(response)


@app.route('/api/Rule/UpdateRule', methods=['PUT'])
def update_rule():
    response = RuleController.update_rule(request.get_json())
    return jsonify(response)


@app.route('/api/Rule/DeleteRule/', methods=['DELETE'])
def delete_rule():
    response = RuleController.delete_rule(request.args.get('id'))
    return response


@app.route('/api/Rule/GetAllRule', methods=['GET'])
def get_all_rules():
    response = RuleController.get_all_rules()
    return jsonify(response)


# @app.route('/api/Section/GetProductivityRules/<int:sectionId>', methods=['GET'])
# def GetProductivityRules(sectionId):
#     response = SectionController.GetProductivityRules(sectionId)
#     return response


##########################ProductController###############################
@app.route('/api/Product/InsertProduct', methods=['POST'])
def InsertProduct():
    jsondata = request.get_json()
    response = ProductController.InsertProduct(jsondata)
    return response


@app.route('/api/Product/InsertBatch', methods=['POST'])
def InsertBatch():
    data = request.get_json()
    response = ProductController.InsertBatch(data)
    return response


@app.route('/api/Product/GetAllProducts', methods=['GET'])
def get_all_products_by_batch_id():
    response = ProductController.get_all_product_by_batch_id(request.args.get('id'))
    return response


@app.route('/api/Product/GetAllBatches', methods=['GET'])
def get_all_batches():
    response = ProductController.get_all_batches()
    return response


@app.route('/api/Product/GetProduct', methods=['GET'])
def GetProduct():
    return jsonify('Ok'), 200


@app.route('/api/Product/UpdateProduct', methods=['PUT'])
def UpdateProduct():
    return jsonify('Ok'), 200


@app.route('/api/Product/DeleteProduct', methods=['DELETE'])
def DeleteProduct():
    return jsonify('Ok'), 200


@app.route('/api/Product/AddRawMaterial', methods=['POST'])
def AddRawMaterial():
    return jsonify('Ok'), 200


@app.route('/api/Product/CalculateYield/<productID>', methods=['GET'])
def CalculateYield(productID):
    return jsonify('Ok'), 200


@app.route('/api/Product/OutputYield/<productID>', methods=['GET'])
def OutputYield(productID):
    return jsonify('Ok'), 200


@app.route('/api/Product/GetDefectedItem', methods=['GET'])
def get_defected_item_by_product():
    result = ProductController.get_defected_product(request.args.get('id'))
    return result


######################EmployeeController#################
@app.route('/api/Employee/InsertEmployee', methods=['POST'])
def insert_employee():
    username = request.form.get('name')
    salary = request.form.get('salary')
    job_role = request.form.get('job_role')
    job_type = request.form.get('job_type')
    date_of_joining = request.form.get('date_of_joining')
    gender = request.form.get('gender')
    user_id = request.form.get('user_id')
    section_id = request.form.get('section_id')
    image_file = request.files.get('image')
    if image_file.filename == '':
        return 'No selected file', 400

    if image_file:
        filename = username + os.path.splitext(image_file.filename)[1]
        image_file.save(os.path.join(app.config['EmployeeImages'], filename))
        data = {'name': username, 'salary': salary, 'jobRole': job_role, 'jobType': job_type
            , 'dateOfJoining': date_of_joining, 'gender': gender, 'userId': user_id, 'sectionId': section_id}
        response = EmployeeController.insert_employee(data, file_name=filename)
        return jsonify(response)
    else:
        return {'message': 'Image is not resource'}


@app.route('/api/Employee/GetAllEmployees', methods=['GET'])
def get_all_employee():
    result = EmployeeController.get_all_employee()
    return result


@app.route('/api/images/<path:image_path>', methods=['GET'])
def get_image(image_path):
    return send_from_directory('EmployeeImages', image_path)


@app.route('/api/Employee/GetEmployee', methods=['GET'])
def get_employee():
    result = EmployeeController.get_employee(request.args.get('id'))
    return result


@app.route('/api/Employee/UpdateEmployee', methods=['PUT'])
def UpdateEmployee():
    return jsonify('Ok'), 200


@app.route('/api/Employee/DeleteEmployee', methods=['DELETE'])
def DeleteEmployee():
    return jsonify('Ok'), 200


@app.route('/api/Employee/MarkAttendance/<int:employeeID>', methods=['POST'])
def MarkAttendance(employeeID):
    return jsonify('Ok'), 200


@app.route('/api/Employee/CalculateFineAndSetRule', methods=['POST'])
def CalculateFineAndSetRule():
    return jsonify('Ok'), 200


@app.route('/api/Employee/GetEmployeeTotalFine', methods=['GET'])
def get_employee_total_fine():
    result = EmployeeController.get_employee_total_fine(request.args.get('id'))
    return result


@app.route('/api/Employee/GetEmployeeAttendance', methods=['GET'])
def get_employee_attendance():
    result = EmployeeController.get_employee_attendance(request.args.get('id'))

    return result


@app.route('/api/Employee/GetViolatedRule', methods=['GET'])
def get_violated_rule():
    response = EmployeeController.get_employee_violation(request.args.get('id'))
    return jsonify(response)


@app.route('/api/Employee/GetEmployeeTotalAttendance/<EmployeeId>', methods=['GET'])
def GetEmployeeTotalAttendance(EmployeeId):
    return jsonify('Ok'), 200


@app.route('/api/Employee/GetEmployeeProductivitySummary/<EmployeeId>/<Start_Date>/<End_Date>', methods=['GET'])
def GetEmployeeProductivitySummary(EmployeeId, Start_Date, End_Date):
    return jsonify('Ok'), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=False)