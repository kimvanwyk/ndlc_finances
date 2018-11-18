import data.mongo_setup
#from data.dues import Dues
#from data.members import Member
from data.cakes import CakeTransfer, CakeStock, CakePayment
from data.transactions import Transaction, AdminTransaction, Account, AdminAccount
from data.market import MarketMonth, MarketDay, list_market_months
from data.members import Member, list_members
from forms import *
from utils import report_months

from flask import Flask, render_template, url_for, redirect, flash, send_from_directory

from datetime import date
import os, os.path
import socket

UDP_PORT = 5001

app = Flask(__name__)
with open('secret_key.txt', 'rb') as fh:
    app.secret_key = fh.read()

data.mongo_setup.global_init()

account_map = {'charity': (Account, Transaction, TransactionForm),
               'admin': (AdminAccount, AdminTransaction, AdminTransactionForm)
               }

cake_transaction_map = {'transfer': (CakeTransferForm, CakeTransfer),
                        'payment': (CakePaymentForm, CakePayment)}

@app.route('/')
def index():
    links = [('Balances', url_for('current_balances'))]
    for acc in Account.objects():
        links.append((f'Add Transaction for {acc.name.capitalize()} Account', url_for('add_transaction', account=acc.name)))
    links.append((f'Add Market Month', url_for('add_market_month')))
    links.append((f'Edit Market Month', url_for('select_market_month',action='edit')))
    links.append((f'Add Cake Transfer', url_for('add_cake_transaction',transaction='transfer')))
    links.append((f'Add Cake Payment', url_for('add_cake_transaction',transaction='payment')))
    links.append((f'Download Report', url_for('build_report')))
    return render_template('index.html', links=links)

@app.route('/balances/<report_month>/')
def balances(report_month):
    results = []
    for acc in Account.objects():
        balances = acc.current_balance(month = report_month)
        results.append([acc.name.capitalize(), report_month])
        results[-1].append((f'{balances[0].date:%d/%m/%y}', f'{balances[0].amount:.2f}'))
        results[-1].append([c[1] for c in acc.transaction_list(reverse=False, month = report_month)])
        results[-1].append((f'{balances[1].date:%d/%m/%y}', f'{balances[1].amount:.2f}'))
    return render_template('balances.html', results=results)
    
@app.route('/balances/current/')
def current_balances():
    report_month = report_months.get_report_months()[1]
    return redirect(url_for('balances', report_month=report_month))
    
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
                                    trans_model(**{k:v for (k,v) in form.data.items() if k not in ('position','csrf_token','submit')}))
            acc.save()
            flash(f'Transaction recorded for {acc.name.capitalize()} account. Balance: R{acc.current_balance()[1].amount:.2f}')
            return redirect(url_for('index'))
        return render_template('basic_form.html', form = form, account = account, caller='add_transaction', args={'account':account})
    return render_template('error.html', message=f'An unexpected error occured')

@app.route('/market/month/add/', methods=('GET', 'POST'))
def add_market_month():
    form = MarketMonthForm()
    if form.validate_on_submit():
        mm = MarketMonth(date=date(year=form.data['year'], month=form.data['month'], day=1), expenses=form.data['expenses'])
        mm.save()
        flash(f'Market Month "{mm.date:%y%m}" added')
        return redirect(url_for('index'))
    return render_template('basic_form.html', form = form, caller='add_market_month', args={})

@app.route('/market/month/edit/<month>/', methods=('GET', 'POST'))
def edit_market_month(month):
    try:
        d = date(year=int(f'20{month[:2]}'), month=int(month[2:]), day=1)
        mm = MarketMonth.objects(date=d).first()
        if not mm:
            raise Exception
    except Exception as e:
        flash(f'"{month} is not a valid date for a market month')
        return redirect(url_for('index'))
    days = mm.list_days()
    if days:
        form = MarketMonthEditForm(month=month, expenses=mm.expenses)
        form.days.choices = days
    else:
        form = MarketMonthEditNoDaysForm(month=month, expenses=mm.expenses)
    if form.validate_on_submit():
        try:
            if form.day_submit.data:
                return redirect(url_for('edit_market_day', month=month, day=form.days.data))
        except AttributeError:
            # not all form types have a day_submit button
            pass
        if form.new_day_submit.data:
            return redirect(url_for('add_market_day', month=month))
        if form.month_submit.data:
            mm.date = date(year=int(f'20{form.month.data[:2]}'), month=int(form.month.data[2:]), day=1)
            mm.expenses = form.expenses.data
            mm.save()
            flash(f'Market Month "{mm.date:%y%m}" edited')
            return redirect(url_for('index'))
    return render_template('basic_form.html', form = form, caller='edit_market_month', args={'month':month})

@app.route('/market/month/<action>/', methods=('GET', 'POST'))
def select_market_month(action, actions = {'edit':'edit_market_month'}):
    if action not in actions:
        flash(f'("{action}" is not a valid action for market month selection')
        return redirect(url_for('index'))
    form = MarketMonthSelectorForm()
    form.month.choices = list_market_months()
    if form.validate_on_submit():
        mm = MarketMonth.objects(id=form.month.data).first()
        return redirect(url_for(actions[action],month=f"{mm.date:%y%m}"))
    return render_template('basic_form.html', form = form, caller='select_market_month', args={'action':action})

@app.route('/market/day/add/<month>/', methods=('GET', 'POST'))
def add_market_day(month):
    form = MarketDayForm()
    if form.validate_on_submit():
        d = date(year=int(f'20{month[:2]}'), month=int(month[2:]), day=1)
        mm = MarketMonth.objects(date=d).first()
        aw = []
        if form.additional_workers.data:
            aw = form.additional_workers.data.split(',')
        md = MarketDay(date=form.date.data, traded=form.traded.data, income=form.income.data,
                       expenses=form.expenses.data, members=[Member.objects(id=i).first() for i in form.members.data],
                       additional_workers=aw)
        mm.days.append(md)
        mm.save()
        flash(f'Market Day "{md.date:%m%d}" added for Market Month "{md.date:%y%m}"')
        return redirect(url_for('index'))
    return render_template('basic_form.html', form = form, caller='add_market_day', args={'month':month})
        
@app.route('/market/day/edit/<month>/<day>/', methods=('GET', 'POST'))
def edit_market_day(month, day):
    try:
        d = date(year=int(f'20{month[:2]}'), month=int(month[2:]), day=1)
        mm = MarketMonth.objects(date=d).first()
        if not mm:
            raise Exception
    except Exception as e:
        flash(f'"{month} is not a valid date for a market month')
        return redirect(url_for('index'))
    days = mm.list_days()
    if day not in [d[0] for d in days]:
        flash(f'"{day} is not a valid market date for market month "{month}"')
        return redirect(url_for('index'))
    d = date(year=int(f'20{month[:2]}'), month=int(day[:2]), day=int(day[2:]))
    for (md_pos, md) in enumerate(mm.days):
        if md.date == d:
            break
    form = MarketDayForm(date=md.date, traded=md.traded, income=md.income,
                         expenses=md.expenses, members=[m.id for m in md.members])
    print([(f.name, f.validate(form), f.data) for f in form])
    if form.validate_on_submit():
        md.date = form.date.data
        md.traded = form.traded.data
        md.income = form.income.data
        md.expenses = form.expenses.data
        md.members = [Member.objects(id=i).first() for i in form.members.data]
        mm.days[md_pos] = md
        mm.save()
        flash(f'Market Day "{md.date:%m%d}" edited for Market Month "{md.date:%y%m}"')
        return redirect(url_for('index'))
    return render_template('basic_form.html', form = form, caller='edit_market_day', args={'month':month, 'day':day})

@app.route('/cake/<transaction>/add/', methods=('GET', 'POST'))
def add_cake_transaction(transaction):
    if transaction not in cake_transaction_map:
        flash(f'("{transaction}" is not a valid transaction for Christmas cakes')
        return redirect(url_for('index'))
    form = cake_transaction_map[transaction][0]()
    if form.validate_on_submit():
        ct = cake_transaction_map[transaction][1](**{k:v for (k,v) in form.data.items() if k not in ('csrf_token','submit')})
        cs = CakeStock.objects().first()
        attr = getattr(cs, f'{transaction}s')
        attr.append(ct)
        cs.save()
        flash(f'Cake {transaction} recorded. Balance: {cs.balance()} cases.')
        return redirect(url_for('index'))
    return render_template('basic_form.html', form = form, caller=f'add_cake_transaction', args={'transaction':transaction})

@app.route('/report/')
def build_report():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM )
    host = os.getenv('REPORT_HOST', 'localhost')
    sock.setblocking(1)
    sock.connect((host, UDP_PORT))
    sock.send('build'.encode()) 
    rec = []
    while True:
        (data, addr) = sock.recvfrom(1024)
        rec.append(data.decode())
        s = ''.join([r for r in rec])
        if '.pdf' in s:
            flash(f'Report file "{s}" downloaded')
            print(s, os.path.join('/tmp', s), os.path.exists(os.path.join('/tmp', s)))
            return send_from_directory('/io', s, as_attachment=True)
        elif 'error' in s:
            flash(f'An error occured building the report')
            return redirect(url_for('index'))
            
