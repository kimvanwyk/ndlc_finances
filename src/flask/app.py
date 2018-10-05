import data.mongo_setup

from data.dues import Dues
from data.members import Member
from data.transactions import Transaction, AdminTransaction, Account, AdminAccount

from flask import Flask, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, RadioField, SelectField
from wtforms.validators import DataRequired

from utils import report_months

app = Flask(__name__)
with open('secret_key.txt', 'rb') as fh:
    app.secret_key = fh.read()

data.mongo_setup.global_init()

account_map = {'charity': Account,
               'admin': AdminAccount
               }

class TransactionForm(FlaskForm):
    trans_type = RadioField(label='Transaction', choices = [(c,c) for c in ('deposit', 'payment')])
    trans_date = DateField(label='Date')
    description = StringField(label='Description')
    amount = DecimalField(label='Amount')
    report_month = SelectField(label='Report Month', choices = [(c,c) for c in report_months.get_report_months()])

@app.route('/transaction/add/<account>/', methods=('GET', 'POST'))
def add_transaction(account):
    try:
        acc = account_map.get(account, None).objects(name=account).first()
    except Exception as e:
        return f'"{account}" is not a valid account name'
    if acc:
        form = TransactionForm()
        if form.validate_on_submit():
            return f'Transaction added'
        return render_template('transaction_add.html', form=form)
    return 'an error occured'

