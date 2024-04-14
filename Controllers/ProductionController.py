import datetime
import time

from flask import jsonify
from sqlalchemy import select, func, join, outerjoin
import os
import io
from flask import send_file
import zipfile
import DBHandler
import Util
from Models.RawMaterial import RawMaterial
from Models.Product import Product
from Models.ProductFormula import ProductFormula
from Models.ProductLink import ProductLink

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
            product = Product(name=data['name'],
                              inspection_angles=data['inspection_angles'],
                              product_number=Util.get_formatted_number(Util.get_first_three_characters(data['name'])))
            session.add(product)
            session.commit()
            product = session.query(Product).where(Product.name == product.name).first()
            if product is None:
                return jsonify({'message': 'An Error Occurred while adding the Product!'}), 500
            materials = data['materials']
            for material in materials:
                mat = ProductFormula(
                    product_number=product.product_number,
                    raw_material_id=material['raw_material_id'],
                    quantity=material['quantity'],
                    unit=material['unit']
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
                batch = Batch(batch_number=Util.get_formatted_number('B'), product_link_id=data["product_link_id"],
                              manufacturing_date=Util.get_current_date())
                session.add(batch)
                stocks = data["stock_list"]
                for stock in stocks:
                    st = StockInBatch(
                        batch_number=batch.batch_number,
                        stock_number=stock["stock_number"]
                    )
                    session.add(st)
                session.commit()
                time.sleep(3)
            return jsonify({'message': 'Batch Added Successfully'})
        except Exception as e:
            return jsonify({'message': str(e)})


def get_all_batches(product_number):
    with DBHandler.return_session() as session:
        try:
            batches = (
                session.query(Batch, ProductLink)
                .join(ProductLink, Batch.product_link_id == ProductLink.id)
                .filter(ProductLink.product_number == product_number)
                .all()
            )
            serialize_batches = []
            for batch, product_link in batches:
                batch_yield = batch.batch_yield
                rejection_tolerance = product_link.rejection_tolerance
                if (100 - batch_yield) > rejection_tolerance:
                    status = 1
                else:
                    status = 0

                serialize_batches.append({
                    'batch_number': batch.batch_number,
                    'status': status
                })

            return jsonify(serialize_batches), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def get_batch(batch_number):
    with DBHandler.return_session() as session:
        try:

            batch, productLink = (
                session.query(Batch, ProductLink)
                .join(ProductLink, ProductLink.id == Batch.product_link_id)
                .filter(Batch.batch_number == batch_number)
                .one()
            )

            batch_yield = batch.batch_yield
            rejection_tolerance = productLink.rejection_tolerance
            if (100 - batch_yield) > rejection_tolerance:
                status = 1
            else:
                status = 0

            serialize_batch = {
                'batch_number': batch.batch_number,
                'status': status,
                'date': datetime.datetime.strptime(str(batch.manufacturing_date), "%Y-%m-%d").strftime("%x"),
                'total_piece': '',
                'defected_piece': '',
                'rejection_tolerance': productLink.rejection_tolerance,
                'batch_yield': batch.batch_yield
            }

            return jsonify(serialize_batch), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def get_all_products():
    with DBHandler.return_session() as session:
        try:
            products = session.scalars(select(Product)).all()
            serialized_products = [{'product_number': product.product_number, 'name': product.name} for product in
                                   products]
            return jsonify(serialized_products), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def get_formula_of_product(product_number):
    with DBHandler.return_session() as session:
        try:
            raw_materials = (
                session.query(RawMaterial)
                .join(ProductFormula, ProductFormula.raw_material_id == RawMaterial.id)
                .filter(ProductFormula.product_number == product_number)
                .all()
            )
            serialize_raw_materials = [{'raw_material_id': material.id, 'name': material.name, 'quantity': '0 KG'} for
                                       material in raw_materials]
            return jsonify(serialize_raw_materials), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def get_linked_products():
    with DBHandler.return_session() as session:
        try:
            products = session.execute(
                select(Product)
                .select_from(
                    join(Product, ProductLink, Product.product_number == ProductLink.product_number)
                )
            ).scalars().all()
            serialized_products = [{'product_number': product.product_number, 'name': product.name} for product in
                                   products]
            return jsonify(serialized_products), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def get_unlinked_products():
    with DBHandler.return_session() as session:
        try:
            products = session.execute(
                select(Product)
                .select_from(
                    outerjoin(Product, ProductLink, Product.product_number == ProductLink.product_number)
                )
                .where(ProductLink.product_number == None)

            ).scalars().all()
            serialized_products = [{'product_number': product.product_number, 'name': product.name} for product in
                                   products]
            return jsonify(serialized_products), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def link_product(data):
    with DBHandler.return_session() as session:
        try:
            product = ProductLink(**data)
            session.add(product)
            session.commit()
            return jsonify({'message': 'Product Linked Successfully'})
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def add_stock(data):
    with DBHandler.return_session() as session:
        try:
            stock = Stock(**data)
            rawMaterial = session.query(RawMaterial).filter(RawMaterial.id == data['raw_material_id']).first()
            if rawMaterial:
                stock.stock_number = Util.get_formatted_number(Util.get_first_three_characters(rawMaterial.name))
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
            purchase_history = session.query(Stock.stock_number, Stock.purchased_date, Stock.quantity,
                                             Stock.price_per_kg) \
                .filter(Stock.raw_material_id == id) \
                .all()

            serialized_purchase_history = [
                {'stock_number': id, 'purchased_date': datetime.datetime.strptime(str(date), "%Y-%m-%d").strftime("%x"),
                 'quantity': quantity, 'price_per_kg': price}
                for id, date, quantity, price in purchase_history]

            return jsonify(serialized_purchase_history), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def get_all_images(folder_path):
    try:
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    zip_file.write(file_path, os.path.relpath(file_path, folder_path))

        zip_buffer.seek(0)

        return send_file(zip_buffer, mimetype='application/zip', as_attachment=True,
                         download_name=f"{folder_path}.zip")

    except Exception as e:
        return jsonify({'message': str(e)}), 500


def get_images(folder_path):
    try:
        if not os.path.exists(folder_path):
            return jsonify({'message': 'Data not found'}), 404

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    zip_file.write(file_path, os.path.relpath(file_path, folder_path))

        zip_buffer.seek(0)

        return send_file(zip_buffer, mimetype='application/zip', as_attachment=True,
                         download_name=f"{folder_path.split(os.path.sep)[-1]}.zip")

    except Exception as e:
        return jsonify({'message': str(e)}), 500
