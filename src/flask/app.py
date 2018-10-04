import data.mongo_setup

from data.dues import Dues
from data.members import Member
from data.transactions import Transaction, AdminTransaction, Account, AdminAccount

from flask import Flask, render_template
app = Flask(__name__)
data.mongo_setup.global_init()

account_map = {'charity': Account,
               'admin': AdminAccount
               }

@app.route('/transaction/add/<account>/')
def add_transaction(account):
    try:
        acc = account_map.get(account, None).objects(name=account).first()
    except Exception as e:
        # print(f'"{account}" is not a valid account name')
        return f'"{account}" is not a valid account name'
    if acc:
        print(acc)
        return str(acc.name)
    print('an error occured')
    return 'an error occured'
