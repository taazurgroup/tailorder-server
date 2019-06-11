from flask import jsonify, request, current_app
from flask.json import loads, dumps

from . import api
from .. import db
from ..models import Order
from ..escpos import write_order, get_usb


@api.route('/void_line', methods=['POST'])
def void_line():
    order_data = request.get_data(as_text=True)
    order = loads(order_data)

    existing_order = Order.query.get(order.get('id'))

    if existing_order:
        line = order.get('line')
        lines = loads(existing_order.lines)

        lines.pop(line)
        existing_order.lines = dumps(lines)

    db.session.commit()

    return jsonify(Order.to_json(existing_order)), 200


@api.route('/change_table', methods=['POST'])
def change_table():
    order_data = request.get_data(as_text=True)
    order = loads(order_data)

    existing_order = Order.query.get(order.get('id'))

    if existing_order:
        existing_order.table_no = order.get('table')

    db.session.commit()

    return jsonify(Order.to_json(existing_order)), 200


@api.route('/cancel_order', methods=['POST'])
def cancel_order():
    order_data = request.get_data(as_text=True)
    order = loads(order_data)

    existing_order = Order.query.get(order.get('id'))

    if existing_order:
        existing_order.is_cancelled = True

    db.session.commit()

    return jsonify(Order.to_json(existing_order)), 200


@api.route('/complete_order', methods=['POST'])
def complete_order():
    order_data = request.get_data(as_text=True)
    order = loads(order_data)

    existing_order = Order.query.get(order.get('id'))

    if existing_order:
        existing_order.is_fulfilled = True

    db.session.commit()

    return jsonify(Order.to_json(existing_order)), 200


@api.route('/print_order', methods=['POST'])
def print_order():
    order_data = request.get_data(as_text=True)
    order = loads(order_data)

    existing_order = Order.query.get(order.get('id'))

    if existing_order:
        is_usb = current_app.config.get('USB')
        if is_usb:
            usb_config = _get_usb_config(current_app.config)
            usb_printer = get_usb(usb_config)
        write_order(existing_order, usb_printer)

    return jsonify(Order.to_json(existing_order)), 200


@api.route('/orders/')
def get_orders():
    return jsonify([order.to_json() for order in Order.query.filter_by(is_fulfilled=False, is_cancelled=False)])


@api.route('/orders', methods=['POST'])
def new_order():
    order_data = request.get_data(as_text=True)
    order = Order.from_json(loads(order_data))

    existing_order = Order.query.filter_by(table_no=order.table_no, is_fulfilled=False, is_cancelled=False).first()

    if existing_order:
        lines = loads(existing_order.lines)

        new_lines = loads(order.lines)
        lines.extend(new_lines)

        existing_order.lines = dumps(lines)

        order = existing_order

    if not existing_order:
        db.session.add(order)

    db.session.commit()

    return jsonify(Order.to_json(order)), 201


def _get_usb_config(config):
    return {
        'id_vendor': config.get('ID_VENDOR'),
        'id_product': config.get('ID_PRODUCT'),
        'endpoint_in': config.get('ENDPOINT_IN'),
        'endpoint_out': config.get('ENDPOINT_OUT')
    }
