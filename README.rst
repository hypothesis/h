Hypothes.is
###########

About
-----

Hypothes.is brings community peer review to The Internet. It is a web site
and a browser application which enable rich annotation of web content. The
web site acts as both a community and authentication end point as well as a
deployment host for the browser application.

The browser application is based substantially on work by the `Open Knowledge
Foundation`_ on the `Annotator Project`_.

Please join us in `#hypothes.is`_ on freenode_.

Installation
------------

See INSTALL.rst for installation instructions.

Running
-------

Hopefully, installation has gone smoothly. If that's the case, the application
can be started easily with the command `./run.py`. However, for development
it is convenient to automatically reload the application when files are
changed. Thankfully, there's a command for that too:

    $ pserve --reload --monitor-restart development.ini

This command will run the server, reloading the application whenever changes
are made to the source code, and restarting it should it crash for some
reason.

Development
-----------

See `#hypothes.is`_.

License
-------

Hypothes.is is released under the `2-Clause BSD License`_, sometimes referred
to as the "Simplified BSD License" or the "FreeBSD License". Some third-party
components are included. They are subject to their own licenses. All of the
license information can be found in the included LICENSE file.

.. _#hypothes.is: http://webchat.freenode.net/?channels=hypothes.is
.. _freenode: http://freenode.net/
.. _Annotator project: http://okfnlabs.org/annotator/
.. _Open Knowledge Foundation: http://okfn.org/
.. _2-Clause BSD License: http://www.opensource.org/licenses/BSD-2-Clause
