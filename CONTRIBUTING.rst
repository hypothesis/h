Contributing to Development
===========================

Communications
--------------
Please be courteous and respectful in your communication on IRC
(`#hypothes.is`_ on `freenode.net`_), the mailing list (`subscribe`_,
`archive`_), and `Github`_. Humor is appreciated, but remember that
some nuance may be lost in the medium and plan accordingly.

When writing commit messages, please bear the following in mind:

* http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html
* https://github.com/blog/831-issues-2-0-the-next-generation

Please minimize issue gardening by using the GitHub syntax for closing
issues with commit messages.

If you plan to be an active contributor please join our mailing list
to coordinate development effort. This coordination helps us avoid
duplicating efforts and raises the level of collaboration. For small
fixes, feel free to open a pull request without any prior discussion.

Licensing
---------
Before submitting significant contributions, we ask that sign one of
our Contributor License Agreements. This practice ensures that the
rights of contributors to their contributions are preserved and
protects the ongoing availability of the project and a commitment to
make it available for anyone to use with as few restrictions as
possible.

There is a version for individuals
[`HTML <http://hypothes.is/contribute/individual-cla>`_ or
`PDF <http://hypothes.is/docs/Hypothes.is%20Project-Individual.pdf>`_]
and a version for those making contributions on behalf of an employer
[`HTML <http://hypothes.is/contribute/entity-cla>`_ or
`PDF <http://hypothes.is/docs/Hypothes.is%20Project-Entity.pdf>`_].

A completed form can either be sent by electronic mail to
license@hypothes.is or via conventional mail at the address below. If
you have any questions, please contact us.

::

    Hypothes.is Project
    2261 Market St #632
    SF, CA 94114

Code Style
----------
Notes on code style follow for the different languages used in the
project. Most important, though, is to follow the style of the code
you are modifying, if your edits are not new files.

Please stick to strict, 80-column line limits except for small
exceptions that would still be readable if they were truncated.

Eliminate trailing whitespace wherever possible.

Python
^^^^^^
Strict PEP8_. The project also adheres closely to the
`Google Python Style Guide`_.

JavaScript
^^^^^^^^^^
Generally, no semi-colons are used. This may change. If you're
starting a new file, do what you like. Like with Python, please follow
the `Google JavaScript Style Guide`_. Additionally, Python-like
spacing is followed for blank lines.

HTML and CSS
^^^^^^^^^^^^^
Once again, the `Google HTML/CSS Style Guide`_ is the place to look.

CoffeeScript
^^^^^^^^^^^^^
As JavaScript, above. Plus these additional suggestions:

Parenthesis are Lisp over ALGOL, except when chaining:

Yes::

    (merge (parse object))
    $(this).css({top: 0}).addClass('red')

No::

    merge(parse(object))

Use implicit returns wherever possible. For instance, a good exception
would be when using return to short circuit a function on an error
condition.

Yes::

    if this
        that
    else
        theOtherThing

No::

    if this
        return that
    else
        return theOtherThing

AngularJS
^^^^^^^^^
Bare attribute names are used unless the directive is not namespaced.

Yes::

    <a href="" ng-click="foo()">Click me!</a>
    <span data-custom-directive="bar">Data Attribute Used Here</span>
    <span my-custom-directive="bar">Custom directive has "my" prefix</span>

No::

    <a href="" data-ng-click="foo()">Click me!</a>
    <span custom-directive="bar">Bad: No Data Attribute Used Here</span>

Committing Policy
-----------------
Committers are those with push access to the `main repository`. These
people should feel free to commit small changes in good faith. It is
expected that these people should read upstream commits made by others
when they feel qualified to review the material and comment with any
objections, questions or suggestions. In general, these commits should
be uncontroversial and do not require up front code review.

Larger changes, and changes being submitted by non-committers, should
follow the branching and merging strategy outlined in the next section.

Branching and Pull Requests
---------------------------
For any non-trivial changes, please create a branch for review. Fork
the main repository and create a local branch. Later, when the branch
is ready for review, push it to a fork and submit a pull request.

Please use the recommended naming policy for branches as it makes it
easier to follow the history back to issues. The recommended template
is <issue name>-<slug>.
 
For instance, 43-browser-extensions would be a branch to address issue
#43, which is to create browser extensions.

Discussion and review in the pull request is normal and expected. By
using a separate branch, it is possible to push new commits to the
pull request branch without mixing new commits from other features or
mainline development.

Please try hard to keep extraneous commits out of pull requests so
that it is easy to see the intent of the patch!

Please do not merge on feature branches. Feature branches should merge
into upstream branches, but never contain merge commits in the other
direction. Consider using '--rebase' when pulling if you must keep
a long-running branch up to date. It is better to start a new branch
and, if applicable, a new pull request when performing this action on
branches you have published.

.. _#hypothes.is: http://webchat.freenode.net/?channels=hypothes.is
.. _freenode.net: http://freenode.net/
.. _subscribe: mailto:dev+subscribe@list.hypothes.is
.. _archive: http://list.hypothes.is/archive/dev
.. _Github: http://github.com/hypothesis/h
.. _PEP8: http://www.python.org/dev/peps/pep-0008/
.. _Google Python Style Guide: https://google-styleguide.googlecode.com/svn/trunk/pyguide.html
.. _Google JavaScript Style Guide: https://google-styleguide.googlecode.com/svn/trunk/javascriptguide.xml
.. _Google HTML/CSS Style Guide: https://google-styleguide.googlecode.com/svn/trunk/htmlcssguide.xml
.. _main repository: https://github.com/hypothesis/h

