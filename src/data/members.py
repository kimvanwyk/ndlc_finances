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
        return f'{self.first_name} {self.last_name}'

def list_members():
    return [(str(m.id), str(m)) for m in Member.objects().order_by("last_name")]

if __name__ == '__main__':
    import mongo_setup
    mongo_setup.global_init()
    print(list_members())
