from flask import request, jsonify
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from db import db
from models import StoreModel, TagModel, ItemModel
from schemas import StoreSchema, TagSchema, TagAndItemSchema

blp = Blueprint("tags", __name__, description="Operations on tags")

@blp.route("/stores/<int:store_id>/tags")
class TagsInStore(MethodView):
    @blp.response(200, TagSchema(many=True))
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        return store.tags.all()

    @blp.arguments(TagSchema)
    @blp.response(201, TagSchema(many=False))
    def post(self, tag_data, store_id):
        # if TagModel.querty.filter(TagModel.store_id == store_id, TagModel.name == tag_data["name"]).first():
        #     return abort(409, message=f"Tag {tag_data['name']} already exists")
        tag = TagModel(**tag_data, store_id=store_id)
        try:
            db.session.add(tag)
            db.session.commit()
            return tag, 201
        except IntegrityError:
            return abort(409, message=f"Tag {tag_data['name']} already exists")
        except SQLAlchemyError as e:
            return abort(500, message=f"Unable to create tag: {e}")


@blp.route("/item/<int:item_id>/tags/<int:tag_id>")
class LinkTagsToItem(MethodView):
    @blp.response(201, TagSchema)
    def post(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)
        item.tags.append(tag)
        try:
            db.session.add(item)
            db.session.commit()
            return tag
        except SQLAlchemyError as e:
            return abort(500, message=f"Unable to link tag to item: {e}")

    @blp.response(200, TagAndItemSchema)
    def delete(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)

        try:
            item.tags.remove(tag)
            db.session.add(item)
            db.session.commit()
        except ValueError:
            # This happens if the Tag wasn't linked to the Item in the first place
            abort(400, message="Tag is not currently linked to this item")
        except SQLAlchemyError as e:
            return abort(500, message=f"Unable to unlink tag from item: {e}")
        return {
            "message": f"Tag unlinked from item",
            "tag": tag,
            "item": item
        }

class TagsForItem(MethodView):
    @blp.response(200, TagAndItemSchema(many=True))
    def get(self, item_id):
        item = ItemModel.query.get_or_404(item_id)
        return item.tags.all(), 200


@blp.route("/tags/<int:tag_id>")
class Tag(MethodView):
    @blp.response(200, TagSchema(many=False))
    def get(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)
        return tag
    @blp.response(202, description="Deletes a tag if no item is tagged with it",
                  example={"message": "Tag deleted successfully"})
    @blp.alt_response(400, description="Tag is still linked to an item",
                      example={"message": "Tag is still linked to an item"})
    def delete(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)
        if not tag.items:
            db.session.delete(tag)
            db.session.commit()
            return {"message": f"Tag {tag_id} deleted successfully"}
        else:
            abort(400, message="Tag is still linked to an item")