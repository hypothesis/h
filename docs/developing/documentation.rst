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
