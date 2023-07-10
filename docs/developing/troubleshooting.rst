Development environment troubleshooting
=======================================

Cannot connect to the Docker daemon
-----------------------------------

If you get an error that looks like this when trying to run ``docker``
commands::

 Cannot connect to the Docker daemon. Is the docker daemon running on this host?
 Error: failed to start containers: postgres

it could be because you don't have permission to access the Unix socket that
the docker daemon is bound to. On some operating systems (e.g. Linux) you need
to either:

* Take additional steps during Docker installation to give your Unix user
  access to the Docker daemon's port (consult the installation
  instructions for your operating system on the Docker website), or

* Prefix all ``docker`` commands with ``sudo``.

pyenv errors on macOS
---------------------

``pyenv install`` commands might fail on macOS with error messages such as:

* "symbol(s) not found for architecture x86_64"
* "ERROR: The Python zlib extension was not compiled. Missing the zlib?"

Read `pyenv's Common Build Problems page <https://github.com/pyenv/pyenv/wiki/common-build-problems>`_
for the solutions to these.
