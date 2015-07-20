Code style
##########

Notes on code style follow for the different languages used in the
project. Most important, though, is to follow the style of the code
you are modifying, if your edits are not new files.

Please stick to strict, 80-column line limits except for small
exceptions that would still be readable if they were truncated.

Eliminate trailing whitespace wherever possible.

Linting
-------

We run a variety of analysis tools on the python codebase using the prospector
package. This is run by the CI on each push but can also be run manually
via the ``lint`` make command::

    $ make lint


Python
------
Strict PEP8_. The project also adheres closely to the
`Google Python Style Guide`_.

.. _PEP8: http://www.python.org/dev/peps/pep-0008/
.. _Google Python Style Guide: https://google-styleguide.googlecode.com/svn/trunk/pyguide.html

JavaScript
----------

Generally, no semi-colons are used. This may change. If you're
starting a new file, do what you like. Like with Python, please follow
the `Google JavaScript Style Guide`_. Additionally, Python-like
spacing is followed for blank lines.

.. _Google JavaScript Style Guide: https://google-styleguide.googlecode.com/svn/trunk/javascriptguide.xml

We use a combination of [JSHint](http://jshint.com) and
[JSCS](http://jscs.info) for helping confirm code style conformance.

You can run both from the root of the repo specifying the directory of the
JavaScript files to check::

    $ jshint h/static/scripts/
    $ jscs h/static/scripts/

HTML and CSS
------------

Once again, the `Google HTML/CSS Style Guide`_ is the place to look.

.. _Google HTML/CSS Style Guide: https://google-styleguide.googlecode.com/svn/trunk/htmlcssguide.xml

AngularJS
---------

Our style is loosely based on a synthesis of several community efforts to
document Angular best practices.

For filesystem structure and naming see the `Best Practice Recommendations
for Angular App Structure`_ document.

.. _Best Practice Recommendations for Angular App Structure: https://docs.google.com/document/d/1XXMvReO8-Awi1EZXAXS4PzDzdNvV6pGcuaF4Q9821Es/pub

For additional tips on writing good AngularJS code, see the following two
recommended guides, which differ slightly but are both very good.

* https://github.com/johnpapa/angularjs-styleguide
* https://github.com/toddmotto/angularjs-styleguide
