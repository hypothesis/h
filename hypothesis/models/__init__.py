from apex.models import Base, DBSession

def includeme(config):
    config.scan(__name__)
    config.include('apex')
    config.include('pyramid_tm')
    config.set_request_property(lambda request: DBSession(), 'db', reify=True)
