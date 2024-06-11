import json
import os.path

from flask import Flask, jsonify, request, send_from_directory

from Controllers import ProductionController, EmployeeController, SectionController,AutomationController

app = Flask(__name__)
app.config['EmployeeImages'] = 'EmployeeImages'
app.config['ViolationImages'] = 'ViolationImages'


#%%%%%%%%%%%%%%%%%%%    ProductionController   %%%%%%%%%%%%%%%%%%%%%%%
@app.route('/api/Production/AddRawMaterial', methods=['POST'])
def add_raw_material():
    response = ProductionController.add_raw_material(request.args.get('name'))
    return response


@app.route('/api/Production/UpdateRawMaterial', methods=['PUT'])
def update_raw_material():
    response = ProductionController.update_raw_material(request.get_json())
    return response


@app.route('/api/Production/GetAllRawMaterials', methods=['GET'])
def get_all_raw_materials():
    response = ProductionController.get_all_raw_materials()
    return response


@app.route('/api/Production/AddProduct', methods=['POST'])
def add_product():
    data = request.get_json()
    response = ProductionController.add_product(data)
    return response


@app.route('/api/Production/GetAllProducts', methods=['GET'])
def get_all_products():
    response = ProductionController.get_all_products()
    return response


@app.route('/api/Production/GetLinkedProducts', methods=['GET'])
def get_linked_products():
    response = ProductionController.get_linked_products()
    return response


@app.route('/api/Production/GetUnlinkedProducts', methods=['GET'])
def get_unlinked_products():
    response = ProductionController.get_unlinked_products()
    return response


@app.route('/api/Production/LinkProduct', methods=['POST'])
def link_product():
    data = request.get_json()
    response = ProductionController.link_product(data)
    return response


@app.route('/api/Production/AddStock', methods=['POST'])
def add_stock():
    data = request.get_json()
    response = ProductionController.add_stock(data)
    return response


@app.route('/api/Production/AddBatch', methods=['POST'])
def add_batch():
    data = request.get_json()
    response = ProductionController.add_batch(data)
    return response


@app.route('/api/Production/GetAllBatches', methods=['GET'])
def get_all_batches():
    product_number = request.args.get('product_number')
    response = ProductionController.get_all_batches(product_number)
    return response


@app.route('/api/Production/GetBatchDetails', methods=['GET'])
def get_batch():
    batch_number = request.args.get('batch_number')
    response = ProductionController.get_batch_details(batch_number)
    return response


@app.route('/api/Production/GetFormulaOfProduct', methods=['GET'])
def get_formula_of_product():
    product_number = request.args.get('product_number')
    response = ProductionController.get_formula_of_product(product_number)
    return response


@app.route('/api/Production/GetAllInventory', methods=['GET'])
def get_all_inventory():
    response = ProductionController.get_all_inventory()
    return response


@app.route('/api/Production/GetStockDetailOfRawMaterial', methods=['GET'])
def get_detail_of_raw_material():
    raw_material_id = request.args.get('id')
    raw_material_id = int(raw_material_id)
    response = ProductionController.get_detail_of_raw_material(raw_material_id)
    return response


@app.route('/api/Production/GetAllDefectedImages', methods=['GET'])
def get_all_defected_images():
    product_number = request.args.get('product_number')
    folder_path = f'defected_items\\{product_number}'
    response = ProductionController.get_defected_images(folder_path)
    return response


@app.route('/api/Production/GetDefectedImagesOfBatch', methods=['GET'])
def get_defected_images():
    product_number = request.args.get('product_number')
    batch_number = request.args.get('batch_number')
    folder_path = f'defected_items\\{product_number}\\{batch_number}'
    response = ProductionController.get_defected_images(folder_path)
    return response

@app.route('/api/Production/DefectMonitoring', methods=['POST'])
def process_images():
    images = request.files.getlist('images')
    product_number = request.form.get('product_number')
    batch_number = request.form.get('batch_number')
    response = ProductionController.defect_monitoring(images, product_number, batch_number)
    return response


#%%%%%%%%%%%%%%%%%%%    SectionController   %%%%%%%%%%%%%%%%%%%%%%%
@app.route('/api/Section/InsertSection', methods=['POST'])
def insert_section():
    data = request.get_json()
    response = SectionController.insert_section(data)
    return response


@app.route('/api/Section/GetAllSections', methods=['GET'])
def get_all_section():
    status = request.args.get('status')
    response = SectionController.get_all_sections(int(status))
    return response


@app.route('/api/Section/GetSectionDetail', methods=['GET'])
def get_section_detail():
    section_id = request.args.get('section_id')
    response = SectionController.get_section_detail(section_id)
    return response


@app.route('/api/Section/UpdateSection', methods=['PUT'])
def update_section():
    data = request.get_json()
    response = SectionController.update_section(data)
    return response


@app.route('/api/Section/ChangeSectionAcitivityStatus', methods=['GET'])
def change_section_activity_status():
    section_id = request.args.get('section_id')
    response = SectionController.change_section_activity_status(section_id)
    return response


@app.route('/api/Section/GetAllRule', methods=['GET'])
def get_all_rules():
    response = SectionController.get_all_rules()
    return response


#%%%%%%%%%%%%%%%%%%%    EmployeeController   %%%%%%%%%%%%%%%%%%%%%%%
@app.route('/api/Employee/Login', methods=['GET'])
def login():
    response = EmployeeController.login(username=request.args.get('username'), password=request.args.get('password'))
    return response


@app.route('/api/Employee/AddEmployee', methods=['POST'])
def add_employee():
    if 'files' not in request.files:
        return jsonify({'message': 'No files part'}), 500
    files = request.files.getlist('files')
    if not files:
        return jsonify({'message': 'No files selected'}), 500
    name = request.form.get('name')
    salary = request.form.get('salary')
    username = request.form.get('username')
    password = request.form.get('password')
    job_role = request.form.get('job_role_id')
    job_type = request.form.get('job_type')
    gender = request.form.get('gender')
    section_id = request.form.get('section_id')
    data = {'name': name, 'salary': salary, 'job_role_id': job_role, 'job_type': job_type, 'gender': gender,
            'section_id': section_id, 'username': username, 'password': password, 'images': files}
    response = EmployeeController.add_employee(data)
    return response


@app.route('/api/Employee/GetAllJobRoles', methods=['GET'])
def get_all_job_roles():
    response = EmployeeController.get_all_job_roles()
    return response


@app.route('/api/Employee/GetAllSupervisors', methods=['GET'])
def get_all_supervisors():
    response = EmployeeController.get_all_supervisors()
    return response


@app.route('/api/Employee/GetSupervisorDetail', methods=['GET'])
def get_supervisor_detail():
    supervisor_id = request.args.get('supervisor_id')
    response = EmployeeController.get_supervisor_detail(supervisor_id)
    return response


@app.route('/api/Employee/UpdateSupervisor', methods=['PUT'])
def update_supervisor():
    data = request.get_json()
    response = EmployeeController.update_supervisor(data)
    return response


@app.route('/api/Employee/GetAllEmployees', methods=['GET'])
def get_all_employees():
    section_id = request.args.get('section_id')
    ranking_required = request.args.get('ranking_required')
    response = EmployeeController.get_all_employees(section_id, ranking_required)
    return response


@app.route('/api/Employee/GetEmployeeDetail', methods=['GET'])
def get_employee_detail():
    employee_id = request.args.get('employee_id')
    response = EmployeeController.get_employee_detail(employee_id)
    return response


@app.route('/api/Employee/GetEmployeeAttendance', methods=['GET'])
def get_employee_attendance():
    employee_id = request.args.get('employee_id')
    response = EmployeeController.get_employee_attendance(employee_id)
    return response


@app.route('/api/Employee/MarkAttendance', methods=['GET'])
def mark_attendance():
    employee_id = request.args.get('employee_id')
   #  if 'files' not in request.files:
   #      return jsonify({'message': 'No files part'}), 400
   #  files = request.files.get('files')
   #  if not files:
   #      return jsonify({'message': 'No files selected'}), 400
   #
   #  video_path = os.path.join('temp_videos', 'attendance.mp4')
   #  files.save(video_path)
    response = EmployeeController.mark_attendance(employee_id) #video_path
    # os.remove(video_path)
    return response



@app.route('/api/EmployeeImage/<int:employee_id>/<path:image_path>', methods=['GET'])
def get_image(employee_id,image_path):
    return send_from_directory(f'EmployeeImages/{employee_id}', image_path)


@app.route('/api/Employee/GetAllViolations', methods=['GET'])
def get_all_violations():
    employee_id = request.args.get('employee_id')
    response = EmployeeController.get_employee_violations(employee_id)
    return response

@app.route('/api/ViolationImages/<path:image_path>', methods=['GET'])
def get_violation_image(image_path):
    return send_from_directory('ViolationImages', image_path)

@app.route('/api/Employee/GetViolationDetails', methods=['GET'])
def get_violation_detail():
    violation_id = request.args.get('violation_id')
    response = EmployeeController.get_violation_details(violation_id)
    return response


@app.route('/api/Employee/GetEmployeeSummary', methods=['GET'])
def get_employee_summary():
    employee_id = request.args.get('employee_id')
    date = request.args.get('date')
    response = EmployeeController.get_employee_summary(employee_id, date)
    return response


@app.route('/api/Employee/GetEmployeeProfile', methods=['GET'])
def get_employee_profile():
    employee_id = request.args.get('employee_id')
    response = EmployeeController.get_employee_profile(employee_id)
    return response


@app.route('/api/Employee/UpdateEmployeeProfile', methods=['PUT'])
def update_employee_profile():
    data = request.get_json()
    response = EmployeeController.update_employee_profile(data)
    return response
@app.route('/api/Automation/PredictEmployeeViolation', methods=['POST'])
def predict_employee_violation():
    if 'files' not in request.files:
        return jsonify({'message': 'No files part'}), 400

    files = request.files.getlist('files')
    if not files:
        return jsonify({'message': 'No files selected'}), 400

    file = files[0]
    video_path = os.path.join('temp_videos', 'tempvideo.mp4')
    file.save(video_path)


    # Extract frame from video
    response = AutomationController.detect_employee_violation(video_path)

    if response is None:
        return jsonify({'message': 'Unable to Save Frame'}), 500
    return response



if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)
