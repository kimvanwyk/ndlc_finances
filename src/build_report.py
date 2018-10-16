from datetime import date

import data.mongo_setup
from data.dues import Dues
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
        debit = f'{debit:.2f}' if debit else ''
        if debit and ('Balance' in desc):
            debit = f'\\textbf{{{debit}}}'
        credit = f'{credit:.2f}' if credit else ''
        if credit and ('Balance' in desc):
            credit = f'\\textbf{{{credit}}}'
        out.append((date, desc, debit, credit))

    out = []
    (start_balance, end_balance) = account.current_balance(month)
    add_row(start_balance.date.strftime('%d/%m/%y'), r'\textbf{Balance brought forward}', None, start_balance.amount)
    current_date = start_balance.date
    for t in (t for t in account.transactions if t.report_month == month):
        if current_date == t.trans_date:
            date = ''
        else:
            current_date = t.trans_date
            date = t.trans_date.strftime('%d/%m/%y')
        add_row(date, t.description, t.amount if t.trans_type == 'payment' else None, t.amount if t.trans_type == 'deposit' else None)
    add_row(end_balance.date.strftime('%d/%m/%y'), r'\textbf{Balance of account}', None, end_balance.amount)

    markup = [f'# {account.name.capitalize()} Account as at {end_balance.date:%d %b %Y}']
    markup.append(r'\begin{center}')
    markup.append(r'\begin{tabularx}{\textwidth}{|c|X|r|r|}')
    markup.append('\hhline{|-|-|-|-|}')
    markup.append(f"\\textbf{{Date}} & \\textbf{{Description}} & \\textbf{{Debit}} & \\textbf{{Credit}} \\\\")
    for row in out:
        markup.append('\hhline{|-|-|-|-|}')
        desc = row[1].replace('&', r'\&')
        markup.append(f"{row[0]} & {desc} & {row[2]} & {row[3]} \\\\")
    markup.append('\hhline{|-|-|-|-|}')
    markup.append(r'\end{tabularx}') 
    markup.append(r'\end{center}') 
    return markup

def build_dues_table():
    markup = [f'# Dues as at {date.today():%d %b %Y}']
    rows = [(Cell('Name', bold=True), Cell('Total', bold=True), Cell('Discount', bold=True), Cell('Paid', bold=True))]
    for m in Member.objects().order_by("last_name"):
        rows.append((Cell(f'{m.last_name}, {m.first_name}'), Cell(f'{m.dues.total:.2f}'), Cell(f'{m.dues.discount:.2f}'), Cell(f'{m.dues.paid:.2f}')))
    markup.extend(build_table(('X','r','r','r'), rows))
    return markup

def build_bar_table():
    acc = Account.objects(name='admin').first()
    (sales, purchases) = acc.bar_values()

    markup = [f'# Bar Account as at {date.today():%d %b %Y}']
    markup.extend(build_table(('X','r','r'), ((Cell('Balance brought forward'), Cell(), Cell('0')), (Cell(f'Sales'), Cell(), Cell(f'{sales:.2f}')),
                                              (Cell(f'Purchases'), Cell(f'{purchases:.2f}'), Cell()), (Cell('Excess Income over Expenditure', bold=True), Cell(), Cell(f'{sales-purchases:.2f}', bold=True))))) 
    return markup

def build_balances_table():
    rows = []
    total = 0
    for acc in ('charity', 'admin'):
        acc = Account.objects(name=acc).first()
        bal = acc.current_balance()[1].amount
        total += bal
        rows.append((Cell(acc.name.capitalize()), Cell(f'{bal:.2f}')))
    rows.append((Cell('Total',bold=True), Cell(f'{total:.2f}')))
    markup = [f'# Balances as at {date.today():%d %b %Y}']
    markup.extend(build_table(('X','r'), rows))
    return markup

markup = []
markup.extend(build_transaction_table(Account.objects(name='charity').first(), '1810'))
markup.extend(build_dues_table())
markup.append('\\newpage')
markup.extend(build_transaction_table(Account.objects(name='admin').first(), '1810'))
markup.extend(build_bar_table())
markup.extend(build_balances_table())
with open('markup.txt', 'w') as fh:
    fh.write('\n'.join(markup))
    # python build_report.py && pandoc markup.txt --template no_frills_latex.txt -o markup.pdf
        
