Code quality
############

We run a variety of analysis tools on the python codebase using the prospector
package. This is run by the CI on each push but can also be run manually
via the ``lint`` make command::

    $ make lint

