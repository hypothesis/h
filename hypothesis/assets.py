import os
from os.path import dirname

from fanstatic import Library, Resource, get_library_registry
from js.jquery import jquery
from js.lesscss import LessResource
from which import which

library = Library('hypothesis', 'resources')
get_library_registry().add(library)

if not 'LESSC' in os.environ:
    os.environ['LESSC'] = which('lessc')

# Work aroud bug in js.lesscss, which tries to del os.environ['PYTHONPATH']
old = os.environ.get('PYTHONPATH', '')
if not old:
    os.environ['PYTHONPATH'] = ''
site_styles = LessResource(library, 'stylesheets/site.less')
os.environ['PYTHONPATH'] = old

def includeme(config):
    """Sets up fanstatic and the static view routes"""

    # Set up fanstatic to serve the .less and .coffee files
    fanstatic_settings = {
        'fanstatic.bottom': True,
        'fanstatic.debug': True,
        'fanstatic.publisher_signature': 'assets',
    }
    config.add_settings(**fanstatic_settings)
    config.include('pyramid_fanstatic')

    # Set up the static routes
    config.add_static_view('images', 'hypothesis:resources/images/')
    config.add_static_view('graphics', 'hypothesis:resources/graphics/')
