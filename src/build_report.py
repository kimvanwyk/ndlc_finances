from collections import defaultdict
from datetime import date

import data.mongo_setup
from data.cakes import CakeStock
from data.dues import Dues
from data.market import MarketMonth
from data.members import Member
from data.transactions import Transaction, AdminTransaction, Account, AdminAccount

import attr

data.mongo_setup.global_init()

@attr.s
class Cell():
    val = attr.ib(default='')
    bold = attr.ib(default=False)
    flt = attr.ib(default=False)

    def __getattr__(self, name):
        if name == 'value':
            if self.flt:
                val = f'{self.val:.2f}'
            else:
                val = str(self.val)
            val = val.replace('&', '\&')
            if not self.bold:
                return val
            else:
                return f'\\textbf{{{val}}}'

def build_table(cols, rows):
    hline = f'\\hhline{{{"|-"*len(cols)}|}}'
    markup = []
    markup.append(r'\begin{center}')
    markup.append(f'\\begin{{tabularx}}{{\\textwidth}}{{|{"|".join(cols)}|}}')
    markup.append(hline)
    for r in rows:
        markup.append(f'{" & ".join([c.value for c in r])} \\\\')
        markup.append(hline)
    markup.append(r'\end{tabularx}') 
    markup.append(r'\end{center}') 
    return markup
       
def build_transaction_table(account, month):
    def add_row(date, desc, debit, credit):
        debit = Cell(debit,flt=True) if debit else Cell()
        if debit and desc.bold:
            debit.bold = True
        credit = Cell(credit, flt=True) if credit else Cell()
        if credit and desc.bold:
            credit.bold = True
        rows.append((date, desc, debit, credit))

    rows = [[Cell(txt,bold=True) for txt in ('Date', 'Description', 'Debit', 'Credit')]]
    (start_balance, end_balance) = account.current_balance(month)
    add_row(Cell(start_balance.date.strftime('%d/%m/%y'),bold=True), Cell('Balance brought forward', bold=True), None, start_balance.amount)
    current_date = start_balance.date
    for t in (t for t in account.transactions if t.report_month == month):
        if current_date == t.trans_date:
            date = ''
        else:
            current_date = t.trans_date
            date = t.trans_date.strftime('%d/%m/%y')
        add_row(Cell(date), Cell(t.description), t.amount if t.trans_type == 'payment' else None, t.amount if t.trans_type == 'deposit' else None)
    add_row(Cell(end_balance.date.strftime('%d/%m/%y'),bold=True), Cell('Balance of account', bold=True), None, end_balance.amount)

    markup = [f'# {account.name.capitalize()} Account']
    markup.extend(build_table(('c','X','r','r'), rows))
    return markup

def build_dues_table():
    markup = [f'# Dues']
    rows = [(Cell('Name', bold=True), Cell('Total', bold=True), Cell('Discount', bold=True), Cell('Paid', bold=True))]
    for m in Member.objects().order_by("last_name"):
        rows.append((Cell(f'{m.last_name}, {m.first_name}'), Cell(m.dues.total, flt=True), Cell(m.dues.discount, flt=True), Cell(m.dues.paid, flt=True)))
    markup.extend(build_table(('X','r','r','r'), rows))
    return markup

def build_bar_table():
    acc = Account.objects(name='admin').first()
    (sales, purchases) = acc.bar_values()

    markup = [f'# Bar Account']
    markup.extend(build_table(('X','r','r'), ((Cell('Balance brought forward'), Cell(), Cell('0')), (Cell(f'Sales'), Cell(), Cell(sales, flt=True)),
                                              (Cell(f'Purchases'), Cell(purchases, flt=True), Cell()), (Cell('Excess Income over Expenditure', bold=True), Cell(), Cell(sales-purchases, bold=True, flt=True))))) 
    return markup

def build_balances_table():
    rows = []
    total = 0
    for acc in ('charity', 'admin'):
        acc = Account.objects(name=acc).first()
        bal = acc.current_balance()[1].amount
        total += bal
        rows.append((Cell(acc.name.capitalize()), Cell(bal, flt=True)))
    rows.append((Cell('Total',bold=True), Cell(total, flt=True)))
    markup = [f'# Balances']
    markup.extend(build_table(('X','r'), rows))
    return markup

def double_list():
    return [0,0]

def build_cakes_table():
    cs = CakeStock.objects().first()
    d = defaultdict(double_list)
    for t in cs.transfers[1:]:
        d[t.responsible_party][0] += (t.number * (-1 if t.direction == 'return' else 1))
    for t in cs.payments:
        d[t.responsible_party][1] += t.amount
    keys = list(d.keys())
    keys.sort()
    rows = [(Cell('Lion',bold=True), Cell('Cases Taken',bold=True), Cell('Total Amount',bold=True), Cell('Amount Paid',bold=True), Cell('Amount Owed',bold=True))]
    for k in keys:
        amt = d[k][0] * 110
        rows.append((Cell(k), Cell(int(d[k][0]/12)), Cell(int(amt)), Cell(int(d[k][1])), Cell(int(amt-d[k][1]))))
    markup = [f'# Christmas Cakes']
    markup.extend(build_table(('X','r','r','r','r'), rows))
    markup.append(f'**Cases in stock: {cs.balance()}**\n')
    return markup

def build_market_table():
    mms = MarketMonth.objects.order_by('date')
    tot_income = 0
    tot_expenses = 0
    rows = [((Cell('Date',bold=True), Cell(f'On Duty',bold=True),
                 Cell('Income',bold=True), Cell('Expenses',bold=True), Cell('Net',bold=True)))]
    for mm in mms:
        income = 0
        expenses = 0
        for md in mm.days:
            if md.traded:
                on_duty = "/".join([m.short_name() for m in md.members])
            else:
                on_duty = 'Did not trade'
            rows.append((Cell(f'{md.date:%d/%m/%y}'), Cell(f'{on_duty}'), 
                         Cell(md.income,flt=True), Cell(md.expenses,flt=True), Cell(md.income-md.expenses,flt=True)))
            income += md.income
            expenses += md.expenses
        rows.append((Cell(), Cell('Additional Expenses'),
                     Cell(), Cell(mm.expenses,flt=True), Cell()))
        expenses += mm.expenses
        month = mm.date.strftime('%B').upper()
        rows.append((Cell(), Cell(f'{month} TOTALS',bold=True),
                     Cell(income,bold=True,flt=True), Cell(expenses,bold=True,flt=True), Cell(income-expenses,bold=True,flt=True)))
        tot_income += income
        tot_expenses += expenses
    rows.append((Cell(), Cell(f'YTD TOTALS',bold=True),
                 Cell(tot_income,bold=True,flt=True), Cell(tot_expenses,bold=True,flt=True), Cell(tot_income-tot_expenses,bold=True,flt=True)))
        
    markup = [f'# Market']
    markup.extend(build_table(('c','X','r','r','r'), rows))
    return markup

if 1:
    markup = [f'<<heading:North Durban Lions Club Finance Report as at {date.today():%d %b %Y}>>\n']
    markup.extend(build_transaction_table(Account.objects(name='charity').first(), '1810'))
    markup.extend(build_dues_table())
    markup.append('\\newpage')
    markup.extend(build_transaction_table(Account.objects(name='admin').first(), '1810'))
    markup.extend(build_bar_table())
    markup.extend(build_balances_table())
    markup.append('\\newpage')
    markup.extend(build_market_table())
    markup.extend(build_cakes_table())
    with open('markup.txt', 'w') as fh:
        fh.write('\n'.join(markup))
        # python build_report.py && run_kppe.sh --templates_dir=$PWD/templates/ no_frills_latex markup.txt
