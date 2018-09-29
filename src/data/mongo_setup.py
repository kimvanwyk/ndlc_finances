import mongoengine

def global_init():
    mongoengine.register_connection(alias='default', name='ndlc_finances')
    # mongoengine.connect(alias='core', db='ndlc_finances')
