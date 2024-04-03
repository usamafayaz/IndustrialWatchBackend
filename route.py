import os
from Controllers import  ProductionController
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)
############### Production Controller
@app.route('/api/Production/AddRawMaterial', methods=['POST'])
def add_raw_material():
    response = ProductionController.add_raw_material(request.args.get('name'))
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



if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=False)