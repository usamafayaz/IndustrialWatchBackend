import datetime
import time

from flask import jsonify
from sqlalchemy import select, func

import DBHandler
import Util
from Models.RawMaterial import RawMaterial
from Models.Product import Product
from Models.MaterialInProduct import MaterialInProduct
from Models.StockInBatch import StockInBatch
from Models.Stock import Stock
from Models.Batch import Batch


def add_raw_material(name):
    with DBHandler.return_session() as session:
        try:
            session.add(RawMaterial(name=name))
            session.commit()
            return jsonify({'message': 'Raw Material Added Successfully'}), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def update_raw_material(data):
    with DBHandler.return_session() as session:
        try:
            rawMaterial = session.query(RawMaterial).filter(RawMaterial.id == data['id']).first()
            rawMaterial.name = data['name']
            session.commit()
            return jsonify({'message': 'Raw Material Updated Successfully'}), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def get_all_raw_materials():
    with DBHandler.return_session() as session:
        try:
            materials = session.scalars(select(RawMaterial)).all()
            serialized_materials = [{'id': material.id, 'name': material.name} for material in materials]
            return jsonify(serialized_materials), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def add_product(data):
    with DBHandler.return_session() as session:
        try:
            product = Product(name=data['name'], rejection_tolerance=data['rejection_tolerance'],
                              inspection_angles=data['inspection_angles'],
                              product_number=Util.get_formatted_number('P'))
            session.add(product)
            session.commit()
            product = session.query(Product).where(Product.name == product.name).first()
            if product is None:
                return jsonify({'message': 'An Error Occurred while adding the Product!'}), 500
            materials = data['materials']
            for material in materials:
                mat = MaterialInProduct(
                    product_number=product.product_number,
                    raw_material_id=material['raw_material_id'],
                    quantity=material['quantity'],
                )
                session.add(mat)
                session.commit()
            return jsonify({'message': 'Product Added Successfully.'}), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def add_batch(data):
    with DBHandler.return_session() as session:
        try:
            for i in range(0, int(data["batch_per_day"])):
                batch = Batch(batch_number=Util.get_formatted_number('B'), product_number=data["product_number"],
                              pack_per_batch=data["pack_per_batch"], piece_per_pack=data["piece_per_pack"])
                session.add(batch)
                stocks = data["stock_list"]
                for stock in stocks:
                    st = StockInBatch(
                        batch_number=batch.batch_number,
                        stock_number=stock["stock_number"]
                    )
                    session.add(st)
                session.commit()
                time.sleep(10)
            return jsonify({'message': 'Batch Added Successfully'})
        except Exception as e:
            return jsonify({'message': str(e)})


def get_all_products():
    with DBHandler.return_session() as session:
        try:
            products = session.scalars(select(Product)).all()
            serialized_products = [{'product_number': product.product_number, 'name': product.name} for product in
                                   products]
            return jsonify(serialized_products), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def get_all_batch():
    with DBHandler.return_session() as session:
        try:
            batches = session.scalars(select(Batch)).all()
            serialized_batches = [{'batch_number': batch.batch_number,
                                   'product_number': batch.product_number,
                                   'pack_per_batch': batch.pack_per_batch,
                                   'piece_per_pack': batch.piece_per_pack,
                                   'batch_per_day': batch.batch_per_day} for batch in batches]
            return jsonify(serialized_batches), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def add_stock(data):
    with DBHandler.return_session() as session:
        try:
            stock = Stock(**data)
            stock.stock_number = Util.get_formatted_number('S')
            stock.purchased_date = Util.get_current_date()
            session.add(stock)
            session.commit()
            return jsonify({'message': 'Stock Added Successfully'}), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def get_all_inventory():
    with DBHandler.return_session() as session:
        try:
            total_inventory = session.query(RawMaterial.id, RawMaterial.name, func.sum(Stock.quantity)) \
                .join(Stock, RawMaterial.id == Stock.raw_material_id) \
                .group_by(RawMaterial.id, RawMaterial.name) \
                .all()
            serialized_inventory = [{'raw_material_id': raw_material_id,
                                     'raw_material_name': name,
                                     'total_quantity': total_quantity}
                                    for raw_material_id, name, total_quantity in total_inventory]
            return jsonify(serialized_inventory), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def get_detail_of_raw_material(id):
    with DBHandler.return_session() as session:
        try:
            purchase_history = session.query(Stock.purchased_date, Stock.quantity, Stock.price_per_unit) \
                .filter(Stock.raw_material_id == id) \
                .all()

            serialized_purchase_history = [
                {'purchased_date': datetime.datetime.strptime(str(date), "%Y-%m-%d").strftime("%x"),
                 'quantity': quantity, 'price_per_unit': price}
                for date, quantity, price in purchase_history]

            return jsonify(serialized_purchase_history), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500
