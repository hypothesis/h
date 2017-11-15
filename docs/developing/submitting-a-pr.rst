Submitting a Pull Request
=========================

To submit code or documentation to h you should submit a pull request.

For trivial changes, such as documentation changes or minor errors,
PRs may be submitted directly to master. This also applies to changes
made through the GitHub editing interface. Authors do not need to
sign the CLA for these, or follow fork or branch naming guidelines.

For any non-trivial changes, please create a branch for review. Fork
the main repository and create a local branch. Later, when the branch
is ready for review, push it to a fork and submit a pull request.

Discussion and review in the pull request is normal and expected. By
using a separate branch, it is possible to push new commits to the
pull request branch without mixing new commits from other features or
mainline development.

Some things to remember when submitting or reviewing a pull request:

- Your pull request should contain one logically separate piece of work, and
  not any unrelated changes.

- When writing commit messages, please bear the following in mind:

  * http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html
  * https://github.com/blog/831-issues-2-0-the-next-generation

  Please minimize issue gardening by using the GitHub syntax for closing
  issues with commit messages.

- We recommend giving your branch a relatively short, descriptive,
  hyphen-delimited name. ``fix-editor-lists`` and ``tabbed-sidebar`` are good
  examples of this convention.

- Don't merge on feature branches. Feature branches should merge into upstream
  branches, but never contain merge commits in the other direction.
  Consider using ``--rebase`` when pulling if you must keep a long-running
  branch up to date. It's better to start a new branch and, if applicable, a
  new pull request when performing this action on branches you have published.

- Code should follow our :doc:`coding standards <code-style>`.

- All pull requests should come with code comments. For Python code these
  should be in the form of Python `docstrings`_. For AngularJS code please use
  `ngdoc`_. Other documentation can be put into the ``docs/`` subdirectory, but
  is not required for acceptance.

- All pull requests should come with unit tests. For the time being, functional
  and integration tests should be considered optional if the project does not
  have any harness set up yet.

  For how to run the tests, see :ref:`running-the-tests`.

.. _docstrings: http://legacy.python.org/dev/peps/pep-0257/
.. _ngdoc: https://github.com/angular/angular.js/wiki/Writing-AngularJS-Documentation
