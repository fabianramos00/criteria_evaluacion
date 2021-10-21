from flask_marshmallow import Schema
from marshmallow.fields import Function

from constants import CRITERIA_ITEM_DICT
from models.models import Record


class RecordSchema(Schema):

    last_item_evaluated_name = Function(lambda obj: CRITERIA_ITEM_DICT[obj.last_item_evaluated])

    class Meta:
        model = Record
        fields = (
        'token', 'repository_url', 'repository_names', 'created_on', 'last_updated', 'rating', 'last_item_evaluated',
        'is_completed', 'last_item_evaluated_name')