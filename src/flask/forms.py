import data.mongo_setup
from data.members import Member, list_members
from utils import report_months

from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, RadioField, SelectField, SelectMultipleField, BooleanField, IntegerField, SubmitField
from wtforms.validators import DataRequired

from datetime import date

data.mongo_setup.global_init()

class TransactionForm(FlaskForm):
    trans_type = RadioField(label='Transaction', choices = [(c,c) for c in ('deposit', 'payment')], default='deposit')
    trans_date = DateField(label='Date', default=date.today)
    description = StringField(label='Description')
    amount = DecimalField(label='Amount')
    position = SelectField(label='Insert After')
    report_month = SelectField(label='Report Month', choices = [(c,c) for c in report_months.get_report_months()])
    submit = SubmitField(label='Submit New Transaction')

class CharityTransactionForm(TransactionForm):
    market = BooleanField(label='Market Transaction', default=False)

class AdminTransactionForm(TransactionForm):
    bar = BooleanField(label='Bar Transaction', default=False)

class MarketMonthForm(FlaskForm):
    year = IntegerField(label='Year', default=date.today().year)
    month = IntegerField(label='Month', default=date.today().month)
    expenses = DecimalField(label='Expenses', default=0)
    submit = SubmitField(label='Submit New Market Month')

class MarketMonthEditForm(FlaskForm):
    month = StringField(label='Month')
    expenses = DecimalField(label='Expenses')
    days = SelectField(label='Market Days')
    day_submit = SubmitField(label='Edit Market Day Details')
    month_submit = SubmitField(label='Submit Change in Month Details')
    new_day_submit = SubmitField(label='Add Market Day')

class MarketMonthEditNoDaysForm(FlaskForm):
    month = StringField(label='Month')
    expenses = DecimalField(label='Expenses')
    days = StringField(label='Market Days', default='No market days available for this month')
    month_submit = SubmitField(label='Submit Change in Month Details')
    new_day_submit = SubmitField(label='Add Market Day')

class MarketMonthSelectorForm(FlaskForm):
    month = SelectField(label='Market Months')
    submit = SubmitField(label='Select Market Month')

class MarketDayForm(FlaskForm):
    date = DateField(label='Date', default=date.today)
    members = SelectMultipleField(label='Members', choices=list_members())
    additional_workers = StringField(label='Additional Workers', default='')
    traded = BooleanField(label='Did the market stall trade?', default=True)
    income = DecimalField(label='Income', default=0)
    expenses = DecimalField(label='Expenses', default=0)
    submit = SubmitField(label='Submit Market Day Changes')

class CakeTransferForm(FlaskForm):
    date = DateField(label='Date', default=date.today)
    number = IntegerField(label='Number of Cakes', default=12)
    responsible_party = StringField(label='Responsible Party')
    direction = RadioField(label='Transfer Direction', choices = [(c,c) for c in ('withdrawal', 'return')], default='withdrawal')
    submit = SubmitField(label='Submit Cake Transfer')

class CakePaymentForm(FlaskForm):
    date = DateField(label='Date', default=date.today)
    amount = DecimalField(label='Amount')
    responsible_party = StringField(label='Responsible Party')
    submit = SubmitField(label='Submit Cake Payment')

