import mongoengine
from datetime import datetime
import operator

class Transaction(mongoengine.EmbeddedDocument):
    trans_type = mongoengine.StringField(required=True, choices=('deposit', 'payment'))
    trans_date = mongoengine.DateTimeField(required=True, default=datetime.now)
    description = mongoengine.StringField(max_length=50, required=True)
    amount = mongoengine.DecimalField(required=True)
    report_month = mongoengine.StringField(max_length=10, required=True)

    meta = {
        'db_alias': 'default',
        'allow_inheritance': True
        }

class AdminTransaction(Transaction):
    bar = mongoengine.BooleanField(default=False)

    meta = {
        'db_alias': 'default',
        }

class Account(mongoengine.Document):
    name = mongoengine.StringField(required=True, choices=('charity', 'admin'))
    initial_balance = mongoengine.DecimalField(required=True)
    transactions = mongoengine.EmbeddedDocumentListField(Transaction)

    meta = {
        'db_alias': 'default',
        'collection': 'accounts',
        'allow_inheritance': True
        }

    def current_balance(self, month=None):
        start_balance = self.initial_balance
        balance = start_balance
        got_start = False
        for t in self.transactions:
            if got_start and t.report_month != month:
                break
            if t.report_month == month and not got_start:
                got_start = True
                start_balance = balance
            balance = (operator.add if t.trans_type == 'deposit' else operator.sub)(balance, t.amount)
        return (start_balance, balance)

class AdminAccount(Account):
    def bar_values(self):
        sales = 0
        purchases = 0
        for t in (t for t in self.transactions if t.bar):
            if t.trans_type == 'deposit':
                sales += t.amount
            else:
                purchases += t.amount
        return (sales, purchases)
