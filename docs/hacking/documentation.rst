Writing documentation
#####################

To build the documentation, ensure that Sphinx_ is installed and issue the
```make html``` command from the docs directory:

.. code-block:: bash

    cd docs/
    make html

When the build finishes, you can view the documentation by running a static
web server in the newly generated ``_build/html/`` directory. For example:

.. code-block:: bash

    pushd _build/html/; python -m SimpleHTTPServer; popd

.. _Sphinx: http://sphinx-doc.org/
