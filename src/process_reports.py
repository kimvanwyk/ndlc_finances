from datetime import datetime
import decimal
import glob
import operator

from openpyxl import load_workbook

import data.mongo_setup
data.mongo_setup.global_init()

from data.dues import Dues
from data.members import Member
from data.transactions import Transaction


if 0:
    Transaction.drop_collection()
    settings = {'charity': {'balance':decimal.Decimal(28764.70), 'first_col': 0},
                'admin': {'balance':decimal.Decimal(37369.24), 'first_col': 1}}
    for account in ('charity', 'admin'):
        balance = settings[account]['balance']
        for fn in glob.glob('reports/*.xlsx'):
            wb = load_workbook(filename = fn, data_only=True, guess_types=True)
            sh = wb[account.upper()]
            in_trans = False
            for row in sh.values:
                row = row[settings[account]['first_col']:]
                if all(c is None for c in row):
                    in_trans = False
                if in_trans:
                    if row[0]:
                        date = row[0].date()
                    if row[1] and 'Balance' not in row[1]:
                        for (index, trans_type, op) in ((2, 'payment', operator.sub),
                                                        (3, 'deposit', operator.add)):
                            try:
                                val = row[index].strip()
                            except Exception as e:
                                val = row[index]
                            if val:
                                amt = decimal.Decimal(val)
                                break
                        acct = account
                        if acct == 'admin' and any(c in row[1].lower() for c in ('bar ', 'drinks ')):
                            acct='bar'
                        print(f'{acct} {trans_type} on {date.strftime("%y/%m/%d")}: {amt:.2f}. "{row[1]}". Balance: {balance:.2f}')
                        t = Transaction(account=acct, trans_type=trans_type, trans_date=date,
                                        description=row[1], amount=amt, balance_before=balance,
                                        reported=True)
                        t.save()
                        balance = op(balance, amt)
                # find date info
                if row[0] == 'Date':
                    in_trans = True
        print(f'final balance: {balance:.2f}')

if 0:
    wb = load_workbook(filename = 'reports/1809xx.xlsx', data_only=True, guess_types=True)
    sh = wb['CHARITY']
    in_trans = False
    for row in sh.values:
        if all(c is None for c in row):
            in_trans = False
        if in_trans:
            (ln, fn) = row[1].strip().rsplit(' ', 1)
            d = Dues(total=decimal.Decimal(row[0]), discount=decimal.Decimal(row[2] if row[2] else 0), paid=decimal.Decimal(row[3] if row[3] else 0))
            m = Member(first_name=fn, last_name=ln, dues=d)
            m.save()
        if (row[0] == 'Dues') and (row[1] == 'Name'):
            in_trans = True

