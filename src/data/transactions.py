from datetime import datetime
import decimal
import operator

import attr, attr.validators
import mongoengine

@attr.s
class Balance():
    date = attr.ib(validator=attr.validators.instance_of(datetime))
    amount = attr.ib(validator=attr.validators.instance_of(decimal.Decimal))

    def alter(self, trans_type, value):
        self.amount = (operator.add if trans_type == 'deposit' else operator.sub)(self.amount, value)

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
        start_balance = Balance(self.transactions[0].trans_date, self.initial_balance)
        end_balance = Balance(self.transactions[-1].trans_date, start_balance.amount)
        got_start = False
        for t in self.transactions:
            if got_start and t.report_month != month:
                break
            if t.report_month == month and not got_start:
                got_start = True
                start_balance.amount = end_balance.amount
                start_balance.date = t.trans_date
            end_balance.alter(t.trans_type, t.amount)
            end_balance.date = t.trans_date
        return (start_balance, end_balance)

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
