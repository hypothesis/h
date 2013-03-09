Hypothes.is
###########

About
-----

Hypothes.is brings community peer review to The Internet. It is a web
application which enables rich annotation of web content. The project acts as
a community aggregator for annotations and identity provider[*]_ for annotators.
It also serves embed code for an annotation agent designed with modern web
browsers in mind.

Installation
------------

See INSTALL.rst for installation instructions.

Running
-------

Installation has, hopefully, gone smoothly. If you ran into any problems, be
sure to seek help on IRC or the mailing list. To run the server, simply use
the ``run`` command::

    $ ./run

This command will run the server, reloading the application whenever changes
are made to the source code, and restarting it should it crash for some
reason.

Development
-----------

The project builds heavily on components developed for the `Annotator Project`_
and is structured to encourage upstream contribution where possible. However,
work is required to make Annotator more extensible in order to facilitate
contribution.

Additionally, work is underway to support the data model described by the
`Open Annotation Core`_ specification document.

See the `project wiki`_ for the roadmap and additional information and
join us in `#hypothes.is`_ on freenode_ for discussion.

Those wishing to contribute to the project should also `subscribe`_ to the
development mailing list and read about `contributing`_.

License
-------

Hypothes.is is released under the `2-Clause BSD License`_, sometimes referred
to as the "Simplified BSD License" or the "FreeBSD License". Some third-party
components are included. They are subject to their own licenses. All of the
license information can be found in the included LICENSE file.

.. _Open Annotation Core: http://openannotation.org/spec/core/
.. _project wiki: https://github.com/hypothesis/h/wiki
.. _#hypothes.is: http://webchat.freenode.net/?channels=hypothes.is
.. _freenode: http://freenode.net/
.. _subscribe: mailto:dev+subscribe@list.hypothes.is
.. _contributing: CONTRIBUTING.rst
.. _Annotator project: http://okfnlabs.org/annotator/
.. _Open Knowledge Foundation: http://okfn.org/
.. _2-Clause BSD License: http://www.opensource.org/licenses/BSD-2-Clause
.. [*] Community and identity features are not finished. Help us out by getting
involved.
