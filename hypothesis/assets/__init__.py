import os

from fanstatic import Library, Resource
from js.lesscss import LessResource
from which import which

# Try to find the 'lessc' binary if it wasn't specified in the environment
if not 'LESSC' in os.environ:
    os.environ['LESSC'] = which('lessc')

assets = Library('assets', '.', ignores=['__init__.py*'])

# Work aroud bug in js.lesscss, which tries to del os.environ['PYTHONPATH']
old = os.environ.get('PYTHONPATH', '')
if not old:
    os.environ['PYTHONPATH'] = ''
site_styles = LessResource(assets, 'stylesheets/site.less')
os.environ['PYTHONPATH'] = old

def includeme(config):
    """Sets up fanstatic and the static view routes"""

    # Set up fanstatic to serve the .less and .coffee files
    fanstatic_settings = {
        'fanstatic.bottom': True,
        'fanstatic.publisher_signature': 'assets',
    }
    config.add_settings(**fanstatic_settings)
    config.include('pyramid_fanstatic')

    # Set up the static routes
    config.add_static_view('images', 'hypothesis.assets:images/')
    config.add_static_view('graphics', 'hypothesis.assets:graphics/')
    config.add_static_view('scripts', 'hypothesis.assets:scripts/')
    config.add_static_view('stylesheets', 'hypothesis.assets:stylesheets/')
