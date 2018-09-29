import mongoengine
from datetime import datetime

class Transaction(mongoengine.Document):
    account = mongoengine.StringField(required=True, choices=('charity', 'admin', 'bar'))
    trans_type = mongoengine.StringField(required=True, choices=('deposit', 'payment'))
    trans_date = mongoengine.DateTimeField(required=True, default=datetime.now)
    description = mongoengine.StringField(max_length=50, required=True)
    amount = mongoengine.DecimalField(required=True)
    balance_before = mongoengine.DecimalField(required=True)
    reported = mongoengine.BooleanField(default=False)
    sequence_val = mongoengine.SequenceField()

    meta = {
        'db_alias': 'default',
        'collection': 'transactions'
        }
