import datetime
import io
import json
import os
import threading
import time
import zipfile

import cv2
import numpy as np
from flask import jsonify, send_file
from sqlalchemy import select, func, join, outerjoin
from tqdm import tqdm
from ultralytics import YOLO

import DBHandler
import Util
from Models.Batch import Batch
from Models.Product import Product
from Models.ProductFormula import ProductFormula
from Models.ProductLink import ProductLink
from Models.RawMaterial import RawMaterial
from Models.Stock import Stock
from Models.StockInBatch import StockInBatch


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
            detail_response, status_code = get_batch_details(batchnumber)
            if status_code != 200:
                raise Exception(f"Failed to retrieve batch details: {detail_response.get('message', 'Unknown error')}")
            detail = json.loads(detail_response.data)
            print(f'total items>{detail["total_piece"]}')
            batch = session.query(Batch).filter(Batch.batch_number == batchnumber).first()
            batch.batch_yield = ((detail['total_piece'] - defected_products) / detail['total_piece']) * 100
            batch.defected_pieces = defected_products
            session.commit()
        except Exception as e:
            print(f'Error Occured: {str(e)}')


class_names = {}
class_names_disc = {0: 'casting', 1: 'milling', 2: 'ok', 3: 'tooling'}
class_names_bottle = {0: 'bottle', 1: 'cap', 2: 'label'}
class_names_textile = {0: 'hole', 1: 'yarn defect'}

bottle_conf_thresholds = {
    0: 0.5,
    1: 0.5,
    2: 0.1
}


def defect_monitoring(images, product_number, batch_number):
    try:
        print("Received images list:", images)

        with DBHandler.return_session() as session:
            product = session.query(Product).filter(Product.product_number == product_number).first()
            product_name = product.name.lower()

        total_items = [0] * len(images)
        defected_items_list = [0] * len(images)
        class_counts = {}
        threads = []

        # path = f'defected_items/{product_name}/{product_number}/{batch_number}'
        path = f'defected_items/{product_number}/{batch_number}'

        if not os.path.exists(path):
            os.makedirs(path)

        for i, image in enumerate(images):
            thread = threading.Thread(target=process_image,
                                      args=(
                                          image, total_items, class_counts, defected_items_list, i, path, product_name))
            threads.append(thread)
            thread.start()

        for thread in tqdm(threads, desc="Processing images"):
            thread.join()

        total_items = len(total_items)
        total_defected_items = sum(defected_items_list)
        print('Total Items:', total_items)
        print('Total Defected Items:', total_defected_items)
        classes = []
        for class_id, count in class_counts.items():
            if 'disc' in product_name:
                class_names = class_names_disc
                if class_id != 2:
                    class_name = class_names.get(class_id, f'Class {class_id}')
                    classes.append({class_name: count})
                    print(f'{class_name}: {count}')
            elif 'fabric' in product_name or 'textile' in product_name:
                class_names = class_names_textile
                class_name = class_names.get(class_id, f'Class {class_id}')
                classes.append({class_name:  count})
                print(f'{class_name}: {count}')
            elif 'bottle' in product_name:
                class_names = class_names_bottle
                if class_id != 0:
                    class_name = class_names.get(class_id, f'Class {class_id}')
                    classes.append({class_name: total_items - count})
                    print(f'{class_name}: {total_items - count}')

        response = {
            'total_items': total_items,
            'total_defected_items': total_defected_items,
            'defects': classes
        }
        print(f'response{response}')
        calculate_yield(batch_number, total_items, total_defected_items)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({'message': e})


def process_image(image_file, total_discs_list, class_counts, defected_items_list, index, folder_path, product_name):
    print(f"Thread {index} started")
    total_items = 0
    print(image_file)
    img_stream = image_file.read()
    nparr = np.frombuffer(img_stream, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    frame_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    model_path = ''
    hide_disc_ok = False
    hide_bottle_ok = False

    if 'disc' in product_name:
        model_path = 'trained_models/disk_model.pt'
        class_names = class_names_disc
        hide_disc_ok = True
    elif 'fabric' in product_name or 'textile' in product_name:
        model_path = 'trained_models/textile_defect_detection.pt'
        class_names = class_names_textile
    elif 'bottle' in product_name:
        model_path = 'trained_models/bottle_defect.pt'
        class_names = class_names_bottle
        hide_bottle_ok = True

    img_with_boxes, unique_classes = predict_with_model(frame_rgb, class_counts, model_path)

    if hide_disc_ok:
        if any(class_id != 2 for class_id in unique_classes):
            total_items += 1
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
            save_path = os.path.join(folder_path, f'processed_{timestamp}.jpg')
            cv2.imwrite(save_path, cv2.cvtColor(img_with_boxes, cv2.COLOR_RGB2BGR))

        total_discs_list[index] = total_items
        if any(class_id != 2 for class_id in unique_classes):
            defected_items_list[index] = 1

    elif hide_bottle_ok:
        # has_bottle = any(class_id == 0 for class_id in unique_classes)
        has_cap = any(class_id == 1 for class_id in unique_classes)
        has_label = any(class_id == 2 for class_id in unique_classes)

        if not has_cap or not has_label:
            total_items += 1
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
            save_path = os.path.join(folder_path, f'processed_{timestamp}.jpg')
            cv2.imwrite(save_path, cv2.cvtColor(img_with_boxes, cv2.COLOR_RGB2BGR))

        total_discs_list[index] = total_items
        if not has_cap or not has_label:
            defected_items_list[index] = 1
    else:
        total_items += 1
        if any(class_id == 0 or class_id == 1 for class_id in unique_classes):
            defected_items_list[index] = 1
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
            save_path = os.path.join(folder_path, f'processed_{timestamp}.jpg')
            cv2.imwrite(save_path, cv2.cvtColor(img_with_boxes, cv2.COLOR_RGB2BGR))
        total_discs_list[index] = total_items
        print(f'Returned defected item {defected_items_list}')
    return defected_items_list


def predict_with_model(img, class_counts, model_path):
    model_path = os.path.abspath(model_path)
    model = YOLO(model_path)
    model_lock = threading.Lock()
    unique_classes = set()
    with model_lock:
        results = model.predict(img, save=False, imgsz=640, show_boxes=True, show_labels=True, show=False)

        for result in results:
            boxes = result.boxes
            filtered_result = result

            for box in boxes:
                class_id = int(box.cls)
                conf = float(box.conf.item())
                if 'bottle' in model_path:
                    if conf >= bottle_conf_thresholds.get(class_id, 0):
                        print("bottle==>>", {conf, class_id, bottle_conf_thresholds.get(class_id, 0)})
                        unique_classes.add(class_id)
                        filtered_result = result
                else:
                    unique_classes.add(class_id)
        # if filtered_result is not None:
        img_with_boxes = filtered_result.plot()
        # else:
        #     img_with_boxes = result.plot()

    # Update class_counts only once per class per image
    for class_id in unique_classes:
        if class_id in class_counts:
            class_counts[class_id] += 1
        else:
            class_counts[class_id] = 1
    print("image_with_boxes==>>", img_with_boxes)
    return img_with_boxes, unique_classes


def angles_monitoring(front_image, back_image, side_images):
    defect_classes = [0, 1, 3]  # Classes representing defects
    side_defect_class = 0  # Side cut defect class

    overall_status = "Ok Product"
    class_count = {}
    defects_report = {
        "front": [],
        "back": [],
        "sides": []
    }

    # Predict defects for front image
    f_image, f_classes = predict_with_model(convert_image_to_ndArrary(front_image), class_count,
                                            'trained_models/disk_model.pt')
    for class_id in f_classes:
        if class_id in defect_classes:
            defects_report["front"].append(class_names_disc.get(class_id))
            overall_status = "Defected Product"

    # Predict defects for back image
    b_image, b_classes = predict_with_model(convert_image_to_ndArrary(back_image), class_count,
                                            'trained_models/disk_model.pt')
    for class_id in b_classes:
        if class_id in defect_classes:
            defects_report["back"].append(class_names_disc.get(class_id))
            overall_status = "Defected Product"

    # Predict defects for side images
    for idx, side_image in enumerate(side_images):
        s_image, s_classes = predict_with_model(convert_image_to_ndArrary(side_image), class_count,
                                                'trained_models/side_cut_model.pt')
        for class_id in s_classes:
            if class_id == side_defect_class:
                defects_report["sides"].append({"side": idx + 1, "defect": "side-cut"})
                overall_status = "Defected Product"

    return jsonify({'status': overall_status, 'defects_report': defects_report}), 200


def convert_image_to_ndArrary(image):
    img_stream = image.read()  # Read the file content
    nparr = np.frombuffer(img_stream, np.uint8)  # Read the file content
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)  # Decode the image
    return img
