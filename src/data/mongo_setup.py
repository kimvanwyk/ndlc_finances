import os
import mongoengine

def global_init():
    host = os.getenv('MONGODB_HOST', 'localhost')
    mongoengine.register_connection(alias='default', name='ndlc_finances', host=host)
