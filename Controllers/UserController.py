import json

from sqlalchemy import select

import DBHandler
from Models.User import User
from flask import jsonify
from sqlalchemy.orm import Session


def insert_user(data):
    with DBHandler.return_session() as session:
        try:
            user = User(data['name'], data['name'], data.get('role'))
            session.add(user)
            session.commit()
            return jsonify({'message': 'Inserted Successfully'}), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def get_all_user():
    with DBHandler.return_session() as session:
        try:
            users = session.scalars(select(User))
            serialize_user = [{'id': user.id, 'name': user.name, 'role': user.role} for user in users]
            return jsonify(serialize_user), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500


#
def get_user(user_id):
    with DBHandler.return_session() as session:
        try:
            user = session.scalars(select(User).where(User.id == user_id)).one()
            user_serialized = {'id': user.id, 'name': user.username, 'role': user.role}
            return jsonify(user_serialized), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def update_user(data):
    with DBHandler.return_session() as session:
        try:
            user = session.scalars(select(User).where(User.id == data.get('id'))).one()
            user.username = data.get('name')
            user.password = data.get('password')
            user.role = data.get('role')
            session.commit()
            serialized_user = {'id': user.id, 'name': user.username, 'password': user.password, 'role': user.role}
            return jsonify(serialized_user),200
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def delete_user(user_id):
    with DBHandler.return_session() as session:
        try:
            user = session.scalars(select(User).where(User.id == user_id)).one()
            session.delete(user)
            session.commit()
            return jsonify({'message': 'User Has been Deleted'}), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def login(username, password):
    try:
        session = DBHandler.return_session()
        user = session.query(User).filter(User.username == username, User.password == password).first()

        if user:
            user_data = {
                'id': user.id,
                'name': user.name,
                'username': user.username,
                'password': user.password,
                'role': user.role
            }
            return jsonify(user_data), 200
        else:
            return jsonify({"message": "User not found or incorrect credentials"}), 404
    except Exception as e:
        return {"error": str(e)}, 500
