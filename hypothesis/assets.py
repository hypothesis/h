import os
from os.path import dirname

from fanstatic import Library, Resource, get_library_registry

from js.annotator import library as annotator
from js.jquery import library as jquery
from js.lesscss import LessResource

hypothesis = Library('hypothesis', 'resources')
site_styles = LessResource(hypothesis, 'stylesheets/site.less')

def includeme(config):
    """Sets up fanstatic and the static view routes"""

    # Set up fanstatic to serve the .less and .coffee files
    fanstatic_settings = {
        'fanstatic.bottom': True,
        'fanstatic.publisher_signature': 'assets',
    }
    config.add_settings(**fanstatic_settings)
    config.include('pyramid_fanstatic')

    get_library_registry().add(annotator)
    get_library_registry().add(jquery)
    get_library_registry().add(hypothesis)

    # Set up the static routes
    config.add_static_view('assets/images', 'hypothesis:resources/images/')
    config.add_static_view('assets/graphics', 'hypothesis:resources/graphics/')
