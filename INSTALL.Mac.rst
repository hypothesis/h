Installing Hypothes.is
######################

Hypothes.is currently requires several tools to build and run from scratch.

These instructions have been tested on OSX 10.8.2. 

A couple of dependencies are needed to get started:
+VirtualEnv


In the future, releases will include built versions of static assets for
integrators wanting to produce custom embeddings of the project on their
own sites and the project welcomes packaging efforts to make including
the Hypothes.is service in any framework easy.

The project code itself is a pyramid_ application which can be integrated
into any WSGI_ compatible framework and run on any WSGI web server (such
as gunicorn_ or uWSGI_). Until the project is ready for an alpha release,
it may not be installable from the Python Package Index. Instead, the
application should be built in a virtual environment which can be set up as
follows::

    $ ./bootstrap

The command will set up the development environment and check for development
dependencies. Warnings will be issued for missing dependencies. When this
script runs without successfully, the environment should be prepared. It is
good practice to run this script whenever the source code changes, such as
after pulling new commits from upstream or checking out a new branch that may
have changed (for example: updated) requirements.

You are almost done, but before you can run the server you need to enter the
virtualenv with the following command::
    
    $ source bin/activate

Then install the additional required dependencies with::

    $ pip install -r requirements.txt

NOTE: if you encounter problems during this stage, (such as "ImportError: 
No module named pkg_resources") then you need to install the Python "distribute" 
package inside the virtual environment. To install this package, download distribute_setup.py 
here: http://python-distribute.org/distribute_setup.py and install it while inside the 
vitualenv with the following command:

    $ python distribute_setup.py install

Then run:

    $ pip install -r requirements.txt

Once you have successfully installed the requirements, you'll be able to start 
the server with::

    $ ./run

For building the static assets, requirements currently include CoffeeScript_
and Sass_ with Compass_ installed. These tools are widely available in package
repositories. Check the platform-specific installation instructions for
details.

For production use, the application will use UglifyJS_ and clean-css_ for
minification needs. These are not required when running the project in a
development configuration.

.. _pyramid: http://www.pylonsproject.org/
.. _gunicorn: http://gunicorn.org/
.. _uWSGI: http://projects.unbit.it/uwsgi/
.. _elasticsearch: http://www.elasticsearch.org/
.. _CoffeeScript: http://coffeescript.org/
.. _Sass: http://sass-lang.com/
.. _Compass: http://compass-style.org/
.. _UglifyJS: http://marijnhaverbeke.nl//uglifyjs
.. _clean-css: https://github.com/GoalSmashers/clean-css
