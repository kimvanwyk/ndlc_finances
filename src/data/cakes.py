from datetime import datetime
import decimal

import mongoengine

class CakeTransfer(mongoengine.EmbeddedDocument):
    date = mongoengine.DateTimeField(required=True, default=datetime.now)
    number = mongoengine.IntField(required=True)
    responsible_party = mongoengine.StringField(required=True)
    direction = mongoengine.StringField(required=True, choices=('withdrawal', 'return'), default='withdrawal')

class CakePayment(mongoengine.EmbeddedDocument):
    date = mongoengine.DateTimeField(required=True, default=datetime.now)
    amount = mongoengine.DecimalField(required=True)
    responsible_party = mongoengine.StringField(required=True)

class CakeStock(mongoengine.Document):
    transfers = mongoengine.EmbeddedDocumentListField(CakeTransfer) 
    payments = mongoengine.EmbeddedDocumentListField(CakePayment)
   
    def balance(self):
        return int((sum(ct.number * (-1 if ct.direction == 'withdrawal' else 1)  for ct in self.transfers)) / 12) 
