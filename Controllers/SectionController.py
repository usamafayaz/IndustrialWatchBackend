from datetime import datetime

from flask import jsonify
from sqlalchemy import select

import DBHandler
import Util
from Models.ProductivityRule import ProductivityRule
from Models.Section import Section
from Models.EmployeeSection import EmployeeSection
from Models.Employee import Employee
from Models.SectionRule import SectionRule


def insert_section(data):
    with DBHandler.return_session() as session:
        try:
            section = Section(name=data['name'], status=1, is_sepecial=data['is_special'])
            session.add(section)
            session.commit()
            section = session.query(Section).where(Section.name == section.name).first()
            if section == None:
                return jsonify({'message': 'Section is not Added check input Data please!'}), 500
            apply_special_section_to_all_existing(section_id=section.id)
            rules = data['rules']
            if insert_rules_in_section(rules, section_id=section.id) == False:
                return jsonify({'message': f'Unable to get Rules check input Data please!'}), 500
            return jsonify({'message': 'Section Successfully Added'}), 200

        except Exception as e:
            return jsonify({'message': str(e)}), 500


def insert_rules_in_section(rules, section_id):
    try:
        session = DBHandler.return_session()
        for rule in rules:
            rul = SectionRule(
                section_id=section_id,
                rule_id=rule['rule_id'],
                fine=rule['fine'],
                allowed_time=rule['allowed_time'],
                date_time=datetime.now()
            )
            session.add(rul)
            session.commit()
        return True
    except Exception as e:
        return False


def get_all_sections(status, is_special=False):
    with DBHandler.return_session() as session:
        try:
            if is_special:
                sections = session.query(Section).filter(Section.status == status).all()
            else:
                sections = session.query(Section).filter(Section.status == status).filter(
                    Section.is_sepecial == 0).all()
            # sections = session.query(Section).filter(Section.status == status).all()
            if sections:
                sections_data = []
                for section in sections:
                    data = {
                        'id': section.id,
                        'name': section.name,
                        'status': section.status
                    }
                    sections_data.append(data)
                return jsonify(sections_data), 200
            else:
                return jsonify({'message': 'No sections found with status {}'.format(status)}), 404
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def get_section_detail(id):
    with DBHandler.return_session() as session:
        try:
            section = session.query(Section).filter(Section.id == id).first()
            if section == None:
                return jsonify({'message': 'Section not found'}), 500
            query = session.query(Section, SectionRule, ProductivityRule).join(SectionRule,
                                                                               Section.id == SectionRule.section_id).join(
                ProductivityRule, SectionRule.rule_id == ProductivityRule.id).filter(Section.id == id)
            result = query.all()
            data = {
                'id': section.id,
                'name': section.name,
                'rules': []
            }
            for sec, section_rule, productivity_rule in result:
                data['rules'].append({
                    'rule_id': productivity_rule.id,
                    'rule_name': productivity_rule.name,
                    'allowed_time': str(section_rule.allowed_time),
                    'fine': section_rule.fine
                })
            return jsonify(data), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def change_section_activity_status(id):
    with DBHandler.return_session() as session:
        try:
            section = session.query(Section).filter(Section.id == id).first()
            if section.status == 0:
                section.status = 1
                session.commit()
                return jsonify({'message': 'Section Successfully Activated.'}), 200
            else:
                section.status = 0
                session.commit()
                return jsonify({'message': 'Section Successfully Deactivated.'}), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def update_section(data):
    with DBHandler.return_session() as session:
        try:
            section = Section(
                id=data['id'],
                name=data['name']
            )
            updated_section = session.query(Section).filter(Section.id == section.id).first()
            updated_section.name = section.name
            session.commit()
            # removing old Rules in Section
            old_rules = session.query(SectionRule).filter(SectionRule.section_id == section.id).all()
            for rule in old_rules:
                session.delete(rule)
            session.commit()
            # inserting new rules
            rules = data['rules']
            if insert_rules_in_section(rules, section.id) == False:
                return jsonify({'message': f'Unable to get Rules check input Data please!'}), 500
            return jsonify({'message': f'Section Successfully Updated'}), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def get_all_rules():
    with DBHandler.return_session() as session:
        try:
            rules = session.scalars(select(ProductivityRule)).all()
            serialized_rules = [{'id': rule.id, 'name': rule.name} for rule in rules]
            return jsonify(serialized_rules), 200

        except Exception as e:
            return jsonify({'message': str(e)}), 500


def get_supervisor_section_and_special(employee_id):
    with DBHandler.return_session() as session:
        try:
            sections = session.query(Section).join(EmployeeSection, Section.id == EmployeeSection.section_id).filter(
                Section.status == 1).filter(EmployeeSection.employee_id == employee_id).all()
            if sections:
                sections_data = []
                for section in sections:
                    data = {
                        'id': section.id,
                        'name': section.name,
                        'status': section.status
                    }
                    sections_data.append(data)
                print(f"get_supervisor_section_and_special {sections_data}")
                return jsonify(sections_data), 200
            else:
                return jsonify({'message': "No section found"}), 500
        except Exception as e:
            return jsonify({'message': str(e)}), 500


def apply_special_section_to_all_existing(section_id):
    with DBHandler.return_session() as session:
        try:
            all_existing_employee = session.query(Employee).all()
            for employee in all_existing_employee:
                session.add(
                    EmployeeSection(section_id=section_id, employee_id=employee.id, date_time=Util.get_current_date()))
            session.commit()
            return True
        except Exception as e:
            print(f" Exception for apply_special_section_to_all_existing {str(e)} ")
            return None
