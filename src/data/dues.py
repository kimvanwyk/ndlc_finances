import mongoengine

class Dues(mongoengine.EmbeddedDocument):
    total = mongoengine.DecimalField(required=True)
    discount = mongoengine.DecimalField(required=True)
    paid = mongoengine.DecimalField(required=True)

    meta = {
        'db_alias': 'default',
        }
