import data.mongo_setup

#from data.dues import Dues
#from data.members import Member
from data.transactions import Transaction, AdminTransaction, Account, AdminAccount
from data.market import MarketMonth
from utils import report_months

from flask import Flask, render_template, url_for, redirect, flash
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, RadioField, SelectField, BooleanField, IntegerField
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

class MarketMonthForm(FlaskForm):
    year = IntegerField(label='Year', default=date.today().year)
    month = IntegerField(label='Month', default=date.today().month)
    expenses = DecimalField(label='Expenses', default=0)

account_map = {'charity': (Account, Transaction, TransactionForm),
               'admin': (AdminAccount, AdminTransaction, AdminTransactionForm)
               }

@app.route('/')
def index():
    links = [('Balances', url_for('balances'))]
    for acc in Account.objects():
        links.append((f'Add Transaction for {acc.name.capitalize()} Account', url_for('add_transaction', account=acc.name)))
    links.append((f'Add Market Month', url_for('add_market_month')))
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
        return render_template('transaction.html', form = form, account = account, caller='add_transaction')
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
    
@app.route('/market/month/add/', methods=('GET', 'POST'))
def add_market_month():
    form = MarketMonthForm()
    if form.validate_on_submit():
        mm = MarketMonth(date=date(year=form.data['year'], month=form.data['month'], day=1), expenses=form.data['expenses'])
        mm.save()
        flash(f'Market Month "{mm.date:%y%m}" added')
        return redirect(url_for('index'))
    return render_template('marketmonth.html', form = form, caller='add_market_month')

        
