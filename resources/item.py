import uuid
from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import jwt_required
from db import db
from models import ItemModel
from schemas import ItemSchema, ItemPutSchema

blp = Blueprint("items", __name__, description="Operations on items")

@blp.route("/items/<int:item_id>")
class Item(MethodView):
    @blp.response(200, ItemSchema(many=False))
    def get(self, item_id):
        item = ItemModel.query.get_or_404(item_id)
        return item


    def delete(self, item_id):
        item = ItemModel.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        return jsonify({"message": f"Item {item_id} deleted successfully"}), 200

    @blp.arguments(ItemPutSchema)
    @blp.response(200, ItemSchema(many=False))
    def put(self, item_data, item_id):
        item = ItemModel.query.get(item_id)
        if item:
            item.name = item_data.get("name", item.name)
            item.price = item_data.get("price", item.price)
            db.session.commit()
            return item, 200
        else:
            item = ItemModel(id=item_id, **item_data)
            db.session.add(item)
            db.session.commit()
            return item, 201


@blp.route("/items")
class ItemList(MethodView):
    @blp.response(200, ItemSchema(many=True))
    def get(self):
        return ItemModel.query.all()

    @jwt_required(fresh=True)
    @blp.arguments(ItemSchema)
    @blp.response(201, ItemSchema(many=False))
    def post(self, item_data):
        item = ItemModel(**item_data)
        try:
            db.session.add(item)
            db.session.commit()
            return item, 201
        except SQLAlchemyError as e:
            return abort(500, message=f"Unable to create item: {e}")
