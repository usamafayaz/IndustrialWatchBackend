import datetime
import io
import os
import time
import zipfile

from flask import jsonify, send_file
from sqlalchemy import select, func, join, outerjoin
import numpy as np
import DBHandler
import Util
from Models.Batch import Batch
from Models.Product import Product
from Models.ProductFormula import ProductFormula
from Models.ProductLink import ProductLink
from Models.RawMaterial import RawMaterial
from Models.Stock import Stock
from Models.StockInBatch import StockInBatch
import cv2
from ultralytics import YOLO
import threading
from tqdm import tqdm


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
            stocks = data["stock_list"]
            for stock in stocks:
                stock_numbers = stock['stocks']
                available_quantity = 0
                total_stock = []
                total_stock_quantity = 0
                calculated_required_quantity = 0
                result = session.query(ProductLink).filter(ProductLink.product_number == data["product_number"]).first()
                for number in stock_numbers:
                    st_result = session.query(Stock, ProductFormula) \
                        .join(ProductFormula, ProductFormula.raw_material_id == Stock.raw_material_id) \
                        .filter(Stock.stock_number == number) \
                        .filter(ProductFormula.product_number == result.product_number) \
                        .first()
                    st, pf = st_result
                    total_stock.append(st)
                    total_stock_quantity += st.quantity
                    available_quantity = Util.convert_to_kg(pf.quantity, pf.unit)
                total_products_in_batch = result.packs_per_batch * result.piece_per_pack * int(data['batch_per_day'])
                calculated_required_quantity = total_products_in_batch * available_quantity
                if calculated_required_quantity > total_stock_quantity:
                    raw_material = session.query(RawMaterial).filter(RawMaterial.id == stock['raw_material_id']) \
                        .first()
                    return jsonify({'message': f'Insufficient Quantity for {raw_material.name}'}), 500
                for st in total_stock:
                    if calculated_required_quantity == 0:
                        break
                    elif st.quantity < calculated_required_quantity:
                        calculated_required_quantity -= st.quantity
                        st.quantity = 0
                    elif st.quantity >= calculated_required_quantity:
                        st.quantity -= calculated_required_quantity
                        calculated_required_quantity = 0
                    if st.quantity == 0:
                        st_in_batch = session.query(StockInBatch).filter(
                            StockInBatch.stock_number == st.stock_number).first()
                        if st_in_batch != None:
                            session.delete(st_in_batch)
                            session.commit()
                        session.delete(st)
                    session.commit()

                #     st = StockInBatch(
                #         batch_number=batch.batch_number,
                #         stock_number=stock["stock_number"]
                #     )
                #     session.add(st)
                # session.commit()
            for i in range(0, int(data["batch_per_day"])):
                batch = Batch(batch_number=Util.get_formatted_number('B'), product_link_id=result.id,
                              manufacturing_date=Util.get_current_date(), batch_yield=-1, defected_pieces=0)

                session.add(batch)
                session.commit()
                time.sleep(1)
            return jsonify({'message': 'Batches Created Successfully'}), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500


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
                if batch.defected_pieces != None:
                    if batch_yield == -1:
                        status = 2
                    elif (100 - batch.batch_yield) > (rejection_tolerance):
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


def get_batch_details(batch_number):
    with DBHandler.return_session() as session:
        try:

            batch, productLink = (
                session.query(Batch, ProductLink)
                .join(ProductLink, ProductLink.id == Batch.product_link_id)
                .filter(Batch.batch_number == batch_number)
                .one()
            )
            total_products_in_batch = productLink.packs_per_batch * productLink.piece_per_pack
            if batch.batch_yield is None:
                calculated_yield = round(float((batch.defected_pieces / total_products_in_batch) * 100), 2)
                batch.batch_yield = calculated_yield
                session.commit()
            rejection_tolerance = productLink.rejection_tolerance
            if batch.batch_yield == -1:
                status = 2
            elif (100 - batch.batch_yield) > (rejection_tolerance):
                status = 1
            else:
                status = 0

            serialize_batch = {
                'batch_number': batch.batch_number,
                'status': status,
                'date': datetime.datetime.strptime(str(batch.manufacturing_date), "%Y-%m-%d").strftime("%x"),
                'total_piece': total_products_in_batch,
                'defected_piece': batch.defected_pieces,
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
                session.query(RawMaterial, ProductFormula)
                .join(ProductFormula, ProductFormula.raw_material_id == RawMaterial.id)
                .filter(ProductFormula.product_number == product_number)
                .all()
            )
            serialize_raw_materials = [
                {'raw_material_id': material.id, 'name': material.name,
                 'quantity': str(Util.convert_to_kg(pf.quantity, pf.unit)) + ' KG'} for
                material, pf in raw_materials]
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


def get_defected_images(folder_path):
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


def calculate_yield(batchnumber, total_products, defected_products):
    with DBHandler.return_session() as session:
        try:
            batch = session.query(Batch).filter(Batch.batch_number == batchnumber).first()
            batch.batch_yield = ((total_products-defected_products) / total_products) * 100
            batch.defected_pieces = defected_products
            session.commit()
        except Exception as e:
            print(f'Error Occured: {str(e)}')


class_names = {0: 'casting', 1: 'milling', 2: 'ok', 3: 'tooling'}

def predict_with_model(img, class_counts):
    model_path = os.path.abspath(f'trained_models/disk_model.pt')
    model = YOLO(model_path)
    model_lock = threading.Lock()
    unique_classes = set()
    with model_lock:
        results = model.predict(img, save=False, imgsz=640, show_boxes=True, show_labels=True, show=False)

        for result in results:
            boxes = result.boxes
            for box in boxes:
                class_id = int(box.cls)
                unique_classes.add(class_id)
            img_with_boxes = result.plot()

    # Update class_counts only once per class per image
    for class_id in unique_classes:
        if class_id in class_counts:
            class_counts[class_id] += 1
        else:
            class_counts[class_id] = 1

    return img_with_boxes, unique_classes


def process_image(image_file, total_discs_list, class_counts, defected_items_list, index, folder_path):
    print(f"Thread {index} started")
    total_discs = 0

    img_stream = image_file.read()
    nparr = np.frombuffer(img_stream, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    frame_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    img_with_boxes, unique_classes = predict_with_model(frame_rgb, class_counts)

    if any(class_id != 2 for class_id in unique_classes):
        total_discs += 1
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
        save_path = os.path.join(folder_path, f'processed_{timestamp}.jpg')
        cv2.imwrite(save_path, cv2.cvtColor(img_with_boxes, cv2.COLOR_RGB2BGR))

    total_discs_list[index] = total_discs

    if any(class_id != 2 for class_id in unique_classes):
        defected_items_list[index] = 1


def defect_monitoring(images, product_number, batch_number):
    try:
        with DBHandler.return_session() as session:
                product = session.query(Product).filter(Product.product_number == product_number).first()
                product_name= product.name
        # if 'disc' in product_name:
        #     Todoo
        total_items = [0] * len(images)
        defected_items_list = [0] * len(images)
        class_counts = {}
        threads = []

        path = f'defected_items/{product_name}/{product_number}/{batch_number}'

        if not os.path.exists(path):
            os.makedirs(path)

        for i, image in enumerate(images):
            thread = threading.Thread(target=process_image,
                                      args=(image, total_items, class_counts, defected_items_list, i, path))
            threads.append(thread)
            thread.start()

        for thread in tqdm(threads, desc="Processing images"):
            thread.join()

        total_discs = len(total_items)
        total_defected_items = sum(defected_items_list)
        print('Total Items:', total_discs)
        print('Total Defected Items:', total_defected_items)
        classes = []
        for class_id, count in class_counts.items():
            if class_id != 2:
                class_name = class_names.get(class_id, f'Class {class_id}')
                classes.append({class_name: count})
                print(f'{class_name}: {count}')

        response = {
            'total_discs': total_discs,
            'total_defected_items': total_defected_items,
            'defects': classes
        }
        calculate_yield(batch_number, total_discs, total_defected_items)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({'message': e})
