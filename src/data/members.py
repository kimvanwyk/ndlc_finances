import mongoengine
from dues import Dues

class Member(mongoengine.Document):
    first_name = mongoengine.StringField(required=True, unique_with="last_name")
    last_name = mongoengine.StringField(required=True, unique_with="first_name")
    dues = mongoengine.EmbeddedDocumentField(Dues)

    meta = {
        'db_alias': 'default',
        'collection': 'members'
    }
    
    def __str__(self):
        print(f'{first_name} {last_name}')
