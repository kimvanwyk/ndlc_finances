from datetime import datetime

import mongoengine
from members import Member

class MarketDay(mongoengine.EmbeddedDocument):
    date = mongoengine.DateTimeField(required=True)
    members = mongoengine.ListField(mongoengine.ReferenceField(Member), required=False)
    traded = mongoengine.BooleanField(required=True, default=True)
    income = mongoengine.DecimalField(required=True, default=0)
    expenses = mongoengine.DecimalField(required=True, default=0)

    meta = {
        'db_alias': 'default',
        'collection': 'marketdays'
    }

class MarketMonth(mongoengine.Document):
    date = mongoengine.DateTimeField(required=True)
    expenses = mongoengine.DecimalField(required=True, default=0)
    days = mongoengine.EmbeddedDocumentListField(MarketDay)

    meta = {
        'db_alias': 'default',
        'collection': 'marketmonths'
    }

def list_market_months():
    return [(str(m.id), m.date.strftime("%B '%y")) for m in MarketMonth.objects().order_by("-date")]

if __name__ == '__main__':
    import mongo_setup
    mongo_setup.global_init()
    print(list_market_months())
