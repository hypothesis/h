Writing documentation
=====================

To build the documentation issue the ``make dirhtml`` command from the ``docs``
directory:

.. code-block:: bash

   cd docs
   make dirhtml

When the build finishes you can view the documentation by running a static
web server in the newly generated ``_build/dirhtml`` directory. For example:

.. code-block:: bash

   cd _build/dirhtml; python -m SimpleHTTPServer; cd -

------------------------------------
API Documentation
------------------------------------

The Hypothesis API documentation is rendered using `ReDoc <https://github.com/Rebilly/ReDoc>`_,
a JavaScript tool for generating OpenAPI/Swagger reference documentation.

The documentation-building process above will regenerate API documentation output without intervention,
but if you are making changes to an API description document (e.g. `hypothesis-v1.yaml`
for v1 on the API),you may find it convenient to use the
`ReDoc CLI tool <https://github.com/Rebilly/ReDoc/blob/master/cli/README.md>`_,
which can watch the spec file for changes:

.. code-block:: bash

  npm install -g redoc-cli
  redoc-cli serve [path-to-description-document] --watch
