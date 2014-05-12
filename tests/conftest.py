from pyramid.paster import get_appsettings
import pytest


@pytest.fixture(scope="session")
def settings():
    settings = get_appsettings('development.ini')
    settings['bind'] = 'localhost:4000'
    settings['es.index'] = 'annotator-test'
    settings['sqlalchemy.url'] = 'sqlite:///test.db'
    settings.update({
        'basemodel.should_create_all': 'True',
        'basemodel.should_drop_all': 'True',
    })
    return settings
