import data.mongo_setup
data.mongo_setup.global_init()

from data.dues import Dues
from data.members import Member
from data.transactions import Transaction, AdminTransaction, Account, AdminAccount

def build_transaction_table(account, month):
    def add_row(date, desc, debit, credit):
        debit = f'{debit:.2f}' if debit else ''
        if debit and ('Balance' in desc):
            debit = f'**{debit}**'
        credit = f'{credit:.2f}' if credit else ''
        if credit and ('Balance' in desc):
            credit = f'**{credit}**'
        out.append((date, desc, debit, credit))
        for w in widths.keys():
            widths[w] = max(len(locals()[w]), widths[w])

    out = []
    widths = {'desc': len('Description'),
              'debit': len('Debit'),
              'credit': len('Credit')}
    (start_balance, end_balance) = account.current_balance(month)
    add_row(start_balance.date.strftime('%d/%m/%y'), '**Balance brought forward**', None, start_balance.amount)
    current_date = start_balance.date
    for t in (t for t in account.transactions if t.report_month == month):
        if current_date == t.trans_date:
            date = '        '
        else:
            current_date = t.trans_date
            date = t.trans_date.strftime('%d/%m/%y')
        add_row(date, t.description, t.amount if t.trans_type == 'payment' else None, t.amount if t.trans_type == 'deposit' else None)
    add_row(end_balance.date.strftime('%d/%m/%y'), '**Balance of account**', None, end_balance.amount)

    wdesc = widths['desc']
    wdebit = widths['debit']
    wcredit = widths['credit']
    markup = []
    markup.append(f"+{'-'*10}+{'-'*(wdesc + 2)}+{'-'*(wdebit + 2)}+{'-'*(wcredit + 2)}+")
    markup.append(f"| {'Date':8} | {'Description':{widths['desc']}} | {'Debit':{widths['debit']}} | {'Credit':{widths['credit']}} |")
    markup.append(f"+:{'='*9}+:{'='*(wdesc + 1)}+:{'='*(wdebit + 1)}+:{'='*(wcredit + 1)}+")
    for row in out:
        markup.append(f"| {row[0]} | {row[1]:{widths['desc']}} | {row[2]:{widths['debit']}} | {row[3]:{widths['credit']}} |")
        markup.append(f"+{'-'*10}+{'-'*(wdesc + 2)}+{'-'*(wdebit + 2)}+{'-'*(wcredit + 2)}+")
    return markup

markup = ['# Charity']
markup.extend(build_transaction_table(Account.objects(name='charity').first(), '1810'))
markup.append('\n# Admin')
markup.extend(build_transaction_table(Account.objects(name='admin').first(), '1810'))
# print('\n'.join(markup))
with open('markup.txt', 'w') as fh:
    fh.write('\n'.join(markup))

        
