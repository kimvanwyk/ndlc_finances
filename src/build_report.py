import data.mongo_setup
data.mongo_setup.global_init()

from data.dues import Dues
from data.members import Member
from data.transactions import Transaction, AdminTransaction, Account, AdminAccount

def build_transaction_table(account, month):
    def add_row(date, desc, debit, credit):
        debit = f'{debit:.2f}' if debit else ''
        if debit and ('Balance' in desc):
            debit = f'\\textbf{{{debit}}}'
        credit = f'{credit:.2f}' if credit else ''
        if credit and ('Balance' in desc):
            credit = f'\\textbf{{{credit}}}'
        out.append((date, desc, debit, credit))
        for w in widths.keys():
            widths[w] = max(len(locals()[w]), widths[w])

    out = []
    widths = {'desc': len('Description'),
              'debit': len('Debit'),
              'credit': len('Credit')}
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

    wdesc = widths['desc']
    wdebit = widths['debit']
    wcredit = widths['credit']
    markup = []
    markup = [r'\begin{center}']
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

markup = ['# Charity']
markup.extend(build_transaction_table(Account.objects(name='charity').first(), '1810'))
markup.append('\n# Admin')
markup.extend(build_transaction_table(Account.objects(name='admin').first(), '1810'))
with open('markup.txt', 'w') as fh:
    fh.write('\n'.join(markup))
    # python build_report.py && pandoc markup.txt --template no_frills_latex.txt -o markup.pdf
        
