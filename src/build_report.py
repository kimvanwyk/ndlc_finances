from collections import defaultdict
from datetime import date
from decimal import Decimal

import data.mongo_setup
from data.cakes import CakeStock
from data.dues import Dues
from data.market import MarketMonth
from data.members import Member
from data.transactions import Transaction, AdminTransaction, Account, AdminAccount
from utils import report_months

import attr

data.mongo_setup.global_init()

@attr.s
class Cell():
    val = attr.ib(default=' ')
    bold = attr.ib(default=False)

    def __getattr__(self, name):
        if name == 'value':
            if type(self.val) is Decimal:
                val = f'{self.val:.2f}'
            else:
                val = str(self.val)
            if not self.bold or not val.strip():
                return val
            else:
                return f'**{val}**'

def c(msg=''):
    return Cell(msg)

def b(msg=''):
    return Cell(msg, bold=True)

def build_table(cols, header, rows):
    markup = ['']
    markup.append(f'|{"|".join([c.value for c in header])}|')
    markup.append(f'|{"|".join(cols)}|')
    for r in rows:
        markup.append(f'|{"|".join([c.value for c in r])}|')
    markup.append('')
    return markup
       
def build_transaction_table(account, month):
    def add_row(date, desc, debit, credit):
        debit = c(debit) if debit else c()
        if debit and desc.bold:
            debit.bold = True
        credit = c(credit) if credit else c()
        if credit and desc.bold:
            credit.bold = True
        rows.append((date, desc, debit, credit))

    header = (b(txt) for txt in ('Date', 'Description', 'Debit', 'Credit'))
    rows = []
    (start_balance, end_balance) = account.current_balance(month)
    add_row(b(start_balance.date.strftime('%d/%m/%y')), b('Balance brought forward'), None, start_balance.amount)
    current_date = start_balance.date
    for t in (t for t in account.transactions if t.report_month == month):
        if current_date == t.trans_date:
            date = ''
        else:
            current_date = t.trans_date
            date = t.trans_date.strftime('%d/%m/%y')
        add_row(c(date), c(t.description), t.amount if t.trans_type == 'payment' else None, t.amount if t.trans_type == 'deposit' else None)
    add_row(b(end_balance.date.strftime('%d/%m/%y')), b('Balance of account'), None, end_balance.amount)

    markup = [f'# {account.name.capitalize()} Account']
    markup.extend(build_table((':-',':-----','-:','-:'), header, rows))
    return markup

def build_dues_table():
    markup = [f'# Dues']
    header = (b('Name'), b('Total'), b('Discount'), b('Paid'), b('Owed'))
    rows = []
    for m in Member.objects().order_by("last_name"):
        rows.append((c(f'{m.last_name}, {m.first_name}'), c(m.dues.total), c(m.dues.discount), c(m.dues.paid), c(m.dues.total - (m.dues.discount+m.dues.paid))))
    markup.extend(build_table((':-----','-:','-:','-:','-:'), header, rows))
    return markup

def build_bar_table():
    acc = Account.objects(name='admin').first()
    (sales, purchases) = acc.bar_values()

    markup = [f'# Bar Account']
    markup.extend(build_table((':-----','-:','-:'), [c(),c(),c()],
                              ((b('Balance brought forward'), c(), b('0')), (c(f'Sales'), c(), c(sales)),
                               (c(f'Purchases'), c(purchases), c()), (b('Excess Income over Expenditure'), c(), b(sales-purchases))))) 
    return markup

def build_balances_table():
    rows = []
    total = 0
    for acc in ('charity', 'admin'):
        acc = Account.objects(name=acc).first()
        bal = acc.current_balance()[1].amount
        total += bal
        rows.append((c(acc.name.capitalize()), c(bal)))
    rows.append((b('Total'), b(total)))
    markup = [f'# Balances']
    markup.extend(build_table((':----','-:'), [c(), c()], rows))
    return markup

def double_list():
    return [0,0]

def build_cakes_table():
    cs = CakeStock.objects().first()
    d = defaultdict(double_list)
    for t in [t for t in cs.transfers if 'Stock Received' not in t.responsible_party]:
        d[t.responsible_party][0] += (t.number * (-1 if t.direction == 'return' else 1))
    for t in cs.payments:
        d[t.responsible_party][1] += t.amount
    keys = list(d.keys())
    keys.sort()
    header = (b('Responsible Party'), b('Cakes Taken'), b('Total Amount'), b('Amount Paid'), b('Amount Owed'))
    rows = []
    totals = {'cakes':0, 'amt': 0, 'paid': 0, 'owed':0}
    for k in keys:
        cakes = d[k][0]
        totals['cakes'] += cakes
        v = 110
        if '@R' in k:
            v = int(k.split('@R')[-1].strip('()'))
        amt = int(d[k][0] * v)
        totals['amt'] += amt
        paid = int(d[k][1])
        totals['paid'] += paid
        owed = int(amt-d[k][1])
        totals['owed'] += owed
        rows.append((c(k), c(cakes), c(amt), c(paid), c(owed)))
    rows.append((c(), b(totals['cakes']), b(totals['amt']), b(totals['paid']), b(totals['owed'])))
    markup = [f'# Christmas Cakes']
    markup.extend(build_table((':-----','-:','-:','-:','-:'), header, rows))
    markup.append(f'**Cakes in stock: {cs.balance()}**\n')
    markup.append(f'Note that some cake payments for the Golden Hours market may be included in market takings and not accurately reflected here.\n')
    return markup

def build_market_expenses_table():
    header = (b('Date'), b(f'Expense'),b('Amount'))
    rows = []
    (additional_expenses, total_additional_expense) = Account.objects(name='charity').first().get_market_expenses()
    rows = []
    for exp in additional_expenses:
        rows.append((c(f'{exp.trans_date:%d/%m/%y}'),c(f'{exp.description}'),c(exp.amount)))
    rows.append((c(), b('TOTAL ADDITIONAL EXPENSES'),b(total_additional_expense)))
    markup = [f'# Market', '## Additional Market Expenses']
    markup.extend(build_table((':-',':-----','-:'), header, rows))
    return markup

def build_market_trading_table():
    tot_income = 0
    tot_expenses = 0
    header = (b('Market Date'), b(f'On Duty'),
             b('Income'), b('Expenses'), b('Net'))
    rows = []

    (additional_expenses, total_additional_expense) = Account.objects(name='charity').first().get_market_expenses()
    mms = MarketMonth.objects.order_by('date')
    for mm in mms:
        income = 0
        expenses = 0
        for md in mm.days:
            if md.traded:
                on_duty = "/".join([m.short_name() for m in md.members] + md.additional_workers)
            else:
                on_duty = 'Did not trade'
            rows.append((c(f'{md.date:%d/%m/%y}'), c(f'{on_duty}'), 
                         c(md.income), c(md.expenses), c(md.income-md.expenses)))
            income += md.income
            expenses += md.expenses
        month = mm.date.strftime('%B').upper()
        rows.append((c(), b(f'{month} TOTALS'),
                     b(income), b(expenses), b(income-expenses)))
        tot_income += income
        tot_expenses += expenses
    rows.append((c(), b('TOTAL ADDITIONAL EXPENSES'), c(), b(total_additional_expense), c()))
    tot_expenses += total_additional_expense
    rows.append((c(), b(f'YTD TOTALS'),
                 b(tot_income), b(tot_expenses), b(tot_income-tot_expenses)))
        
    markup = ['## Market Trading']
    markup.extend(build_table((':-',':-----','-:','-:','-:'), header, rows))
    return markup

def build_markup_file(month=None):
    if month is None:
        month = report_months.get_report_months()[1]
    markup = [f'<<heading:North Durban Lions Club Finance Report as at {date.today():%d %b %Y}>>\n']
    markup.extend(build_transaction_table(Account.objects(name='charity').first(), month))
    markup.extend(build_transaction_table(Account.objects(name='admin').first(), month))
    markup.append('\\newpage')
    markup.extend(build_market_expenses_table())
    markup.extend(build_market_trading_table())
    markup.extend(build_dues_table())
    markup.extend(build_bar_table())
    markup.extend(build_balances_table())
    return '\n'.join(markup)

def write_markup_file(month=None):
    with open('markup.txt', 'w') as fh:
        fh.write(build_markup_file(month))

if __name__ == '__main__':
    write_markup_file()
