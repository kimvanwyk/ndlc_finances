import data.mongo_setup

from data.dues import Dues
from data.members import Member
from data.transactions import Transaction, AdminTransaction, Account, AdminAccount
from utils import report_months

from flask import Flask, render_template, url_for, redirect, flash
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, RadioField, SelectField, BooleanField
from wtforms.validators import DataRequired

from datetime import date

app = Flask(__name__)
with open('secret_key.txt', 'rb') as fh:
    app.secret_key = fh.read()

data.mongo_setup.global_init()

class TransactionForm(FlaskForm):
    trans_type = RadioField(label='Transaction', choices = [(c,c) for c in ('deposit', 'payment')], default='deposit')
    trans_date = DateField(label='Date', default=date.today())
    description = StringField(label='Description')
    amount = DecimalField(label='Amount')
    position = SelectField(label='Insert After')
    report_month = SelectField(label='Report Month', choices = [(c,c) for c in report_months.get_report_months()])

class AdminTransactionForm(TransactionForm):
    bar = BooleanField(label='Bar Transaction', default=False)

account_map = {'charity': (Account, Transaction, TransactionForm),
               'admin': (AdminAccount, AdminTransaction, AdminTransactionForm)
               }

@app.route('/')
def index():
    links = [('Balances', url_for('balances'))]
    for acc in Account.objects():
        links.append((f'Add Transaction for {acc.name.capitalize()} Account', url_for('add_transaction', account=acc.name)))
    return render_template('index.html', links=links)

@app.route('/transaction/add/<account>/', methods=('GET', 'POST'))
def add_transaction(account):
    try:
        (acc_model, trans_model, trans_form) = account_map.get(account, None)
        acc = acc_model.objects(name=account).first()
    except Exception as e:
        return render_template('error.html', message=f'"{account}" is not a valid account name')
    if acc:
        form = trans_form()
        form.position.choices = [(str(n), c) for (n,c) in acc.transaction_list()]
        if form.validate_on_submit():
            acc.transactions.insert(int(form.position.data) + 1,
                                    trans_model(**{k:v for (k,v) in form.data.items() if k not in ('position','csrf_token')}))
            acc.save()
            flash(f'Transaction recorded for {acc.name.capitalize()} account. Balance: R{acc.current_balance()[1].amount:.2f}')
            return redirect(url_for('index'))
        return render_template('transaction_add.html', form = form,account = account)
    return render_template('error.html', message=f'An unexpected error occured')

@app.route('/balances/')
def balances():
    report_month = report_months.get_report_months()[0]
    results = []
    for acc in Account.objects():
        balances = acc.current_balance(month = report_month)
        results.append([acc.name.capitalize(), report_month])
        results[-1].append((f'{balances[0].date:%d/%m/%y}', f'{balances[0].amount:.2f}'))
        results[-1].append([c[1] for c in acc.transaction_list(reverse=False, month = report_month)])
        results[-1].append((f'{balances[1].date:%d/%m/%y}', f'{balances[1].amount:.2f}'))
    return render_template('balances.html', results=results)
    
        
