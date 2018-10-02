from datetime import datetime

import mongoengine

class CakeTransfer(mongoengine.EmbeddedDocument):
    date = mongoengine.DateTimeField(required=True, default=datetime.now)
    number = mongoengine.IntField(required=True)
    responsible_party = mongoengine.StringField(required=True)
    direction = mongoengine.StringField(required=True, choices=('withdrawal', 'return'), default='withdrawal')

class CakeStock(mongoengine.Document):
    initial_stock = mongoengine.IntField(required=True)
    transfers = mongoengine.EmbeddedDocumentListField(CakeTransfer)
    
    def balance(self):
        return int((self.initial_stock - sum(ct.number for ct in self.transfers)) / 12) 
