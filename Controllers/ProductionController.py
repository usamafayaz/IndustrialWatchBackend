from flask import jsonify
from sqlalchemy import select

import DBHandler
from Models.RawMaterial import RawMaterial
from Models.Product import Product
from Models.MaterialInProduct import MaterialInProduct

def add_raw_material(name):
    with DBHandler.return_session() as session:
        try:
            session.add(RawMaterial(name=name))
            session.commit()
            return jsonify({'message':'Raw Material Added Successfully'}),200
        except Exception as e:
            return jsonify({'message':str(e)}),500

def get_all_raw_materials():
    with DBHandler.return_session() as session:
        try:
            materials = session.scalars(select(RawMaterial)).all()
            serialized_materials = [{'id': material.id, 'name': material.name} for material in materials]
            return jsonify({'data':serialized_materials}),200
        except Exception as e:
            return jsonify({'message':str(e)}),500

def add_product(data):
    with DBHandler.return_session() as session:
        try:
            product = Product(name=data['name'],rejection_tolerance=data['rejection_tolerance'], inspection_angles=data['inspection_angles'])
            session.add(product)
            session.commit()
            product = session.query(Product).where(Product.name == product.name).first()
            if product == None:
                return jsonify({'message': 'An Error Occured while adding the Product!'}), 500
            materials= data['materials']
            for material in materials:
                mat = MaterialInProduct(
                    product_id=product.id,
                    raw_material_id=material['raw_material_id'],
                    quantity=material['quantity'],
                )
                session.add(mat)
                session.commit()
            return jsonify({'message':'Product Added Successfully.'}),200
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def get_all_products():
    with DBHandler.return_session() as session:
        try:
            products=session.scalars(select(Product)).all()
            serialized_products = [{'id': product.id, 'name': product.name} for product in products]
            return jsonify({'data': serialized_products}), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500
