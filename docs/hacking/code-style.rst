Code style
##########

This section contains some code style guidelines for the different programming
languages used in the project.


Python
------

Follow `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_, the linting tools
below can find PEP 8 problems for you automatically.

Docstrings
``````````

All public modules, functions, classes, and methods should normally have
docstrings. See `PEP 257 <https://www.python.org/dev/peps/pep-0257/>`_ for
general advice on how to write docstrings (although we don't write module
docstrings that describe every object exported by the module).

The ``pep257`` tool (which is run by ``prospector``, see below) can point out
PEP 257 violations for you.

It's good to use Sphinx references in docstrings because they can be syntax
highlighted and hyperlinked when the docstrings are extracted by Sphinx into
HTML documentation, and because Sphinx can print warnings for references that
are no longer correct:

* Use `Sphinx Python cross-references <http://www.sphinx-doc.org/en/stable/domains.html#cross-referencing-python-objects>`_
  to reference other Python modules, functions etc. from docstrings (there are
  also Sphinx domains for referencing
  objects from other programming languages, such as
  `JavaScript <http://www.sphinx-doc.org/en/stable/domains.html#the-javascript-domain>`_).

* Use `Sphinx info field lists <http://www.sphinx-doc.org/en/stable/domains.html#info-field-lists>`_
  to document parameters, return values and exceptions that might be raised.

* You can also use `reStructuredText <http://www.sphinx-doc.org/en/stable/rest.html>`_
  to add markup (bold, code samples, lists, etc) to docstrings.


Linting
```````

We recommend running `Flake8 <https://pypi.python.org/pypi/flake8>`_
and `Prospector <https://pypi.python.org/pypi/prospector>`_ over your code to
find bugs and style problems, using the configurations provided in this git
repo. With our configurations Flake8 is faster and less noisy so is nicer to
run more frequently, Prospector is more thorough so it can be run less
frequently and may find some problems that Flake8 missed.

Automated code formatting
`````````````````````````

You can use `YAPF <https://github.com/google/yapf>`_ (along with the YAPF
configuration in this git repo) to automatically reformat Python code.
We don't strictly adhere to YAPF-generated formatting but it can be a useful
convenience.

Additional reading
``````````````````

* Although we don't strictly follow all of it, the
  `Google Python Style Guide <https://google.github.io/styleguide/pyguide.html>`_
  contains a lot of good advice.


JavaScript
----------

Please follow the `Google JavaScript Style Guide`_. Additionally, Python-like
spacing is followed for blank lines.

.. _Google JavaScript Style Guide: https://google-styleguide.googlecode.com/svn/trunk/javascriptguide.xml

We use a combination of `JSHint`_ and
`JSCS`_ for helping confirm code style conformance.

.. _JSHint: http://jshint.com/
.. _JSCS: http://jscs.info/

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
