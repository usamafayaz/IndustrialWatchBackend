import os
from Controllers import ProductionController, UserController
from flask import Flask, jsonify, request, send_from_directory
import  Util
app = Flask(__name__)


############### Production Controller
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

@app.route('/api/Production/GetFormulaOfProduct', methods=['GET'])
def get_formula_of_product():
    product_number=request.args.get('product_number')
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

#####################  User Controller  #################################
@app.route('/api/User/InsertUser', methods=['POST'])
def insert_user():
    data = request.get_json()
    return UserController.insert_user(data)


@app.route('/api/User/GetAllUsers', methods=['GET'])
def get_all_user():
    return jsonify(UserController.get_all_user())


@app.route('/api/User/GetUser', methods=['GET'])
def get_user():
    user_id = request.args.get('id')
    response = UserController.get_user(user_id=user_id)
    return jsonify(response)


@app.route('/api/User/UpdateUser', methods=['PUT'])
def update_user():
    data = request.get_json()
    response = UserController.update_user(data)
    return jsonify(response)


@app.route('/api/User/DeleteUser', methods=['DELETE'])
def delete_user():
    user_id = request.args.get('id')
    print(user_id)
    response = UserController.delete_user(user_id)
    return jsonify(response)


@app.route('/api/User/Login', methods=['GET'])
def login():
    response = UserController.login(username=request.args.get('username'), password=request.args.get('password'))
    return response

#####################  Supervisor Controller  #################################
#
# @app.route('/api/Supervisor/GetAllSupervisor', methods=['get'])
# def get_all_supervisors():
#     response = SupervisorController.get_all_supervisors()
#     return response
#
#
# @app.route('/api/Supervisor/InsertSupervisor', methods=['post'])
# def insert_supervisor():
#     data = request.get_json()
#     response = SupervisorController.insert_supervisor(data)
#     return response
#
#
# @app.route('/api/Supervisor/DeleteSupervisor', methods=['delete'])
# def DeleteSupervisor():
#     response = SupervisorController.delete_supervisor(request.args.get('id'))
#     return response
#
#
# @app.route('/api/Supervisor/UpdateSupervisor', methods=['put'])
# def update_supervisor():
#     data = request.get_json()
#     response = SupervisorController.update_supervisor(data)
#     return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)
