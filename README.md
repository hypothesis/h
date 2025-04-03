<a href="https://github.com/hypothesis/h/actions/workflows/ci.yml?query=branch%3Amain"><img src="https://img.shields.io/github/actions/workflow/status/hypothesis/h/ci.yml?branch=main"></a>
<a><img src="https://img.shields.io/badge/python-3.12-success"></a>
<a href="https://github.com/hypothesis/h/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-BSD--2--Clause-success"></a>
<a href="https://github.com/hypothesis/cookiecutters/tree/main/pyramid-app"><img src="https://img.shields.io/badge/cookiecutter-pyramid--app-success"></a>
<a href="https://black.readthedocs.io/en/stable/"><img src="https://img.shields.io/badge/code%20style-black-000000"></a>

# h

h is the web app that serves most of the https://hypothes.is/ website, including the web annotations API at https://hypothes.is/api/. The [Hypothesis client](https://github.com/hypothesis/client) is a browser-based annotator that is a client for h's API.

## Community

Join us on Slack ([request an invite](https://slack.hypothes.is) or [log in once you've created an account](https://hypothesis-open.slack.com/)).

If you'd like to contribute to the project, you should also [subscribe](mailto:dev+subscribe@list.hypothes.is)
to the [development mailing list](https://groups.google.com/a/list.hypothes.is/forum/#!forum/dev)
and read our [Contributor's guide](https://h.readthedocs.io/en/latest/developing/).
Then consider getting started on one of the issues that are ready for work.

Please note that this project is released with a [Contributor Code of Conduct](https://github.com/hypothesis/.github/blob/main/CODE_OF_CONDUCT.md).
By participating in this project you agree to abide by its terms.

## Setting up Your h Development Environment

First you'll need to install:

* [Git](https://git-scm.com/).
  On Ubuntu: `sudo apt install git`, on macOS: `brew install git`.
* [GNU Make](https://www.gnu.org/software/make/).
  This is probably already installed, run `make --version` to check.
* [pyenv](https://github.com/pyenv/pyenv).
  Follow the instructions in pyenv's README to install it.
  The **Homebrew** method works best on macOS.
  The **Basic GitHub Checkout** method works best on Ubuntu.
  You _don't_ need to set up pyenv's shell integration ("shims"), you can
  [use pyenv without shims](https://github.com/pyenv/pyenv#using-pyenv-without-shims).
* [Docker Desktop](https://www.docker.com/products/docker-desktop/).
  On Ubuntu follow [Install on Ubuntu](https://docs.docker.com/desktop/install/ubuntu/).
  On macOS follow [Install on Mac](https://docs.docker.com/desktop/install/mac-install/).
* [Node](https://nodejs.org/) and npm.
  On Ubuntu: `sudo snap install --classic node`.
  On macOS: `brew install node`.
* [Yarn](https://yarnpkg.com/): `sudo npm install -g yarn`.

Then to set up your development environment:

```terminal
git clone https://github.com/hypothesis/h.git
cd h
make services
make devdata
make help
```

See the [Contributor's guide](https://h.readthedocs.io/en/latest/developing/) for further instructions on setting up a development environment and contributing to h.

## Changing the Project's Python Version

To change what version of Python the project uses:

1. Change the Python version in the
   [cookiecutter.json](.cookiecutter/cookiecutter.json) file. For example:

   ```json
   "python_version": "3.10.4",
   ```

2. Re-run the cookiecutter template:

   ```terminal
   make template
   ```

3. Re-compile the `requirements/*.txt` files.
   This is necessary because the same `requirements/*.in` file can compile to
   different `requirements/*.txt` files in different versions of Python:

   ```terminal
   make requirements
   ```

4. Commit everything to git and send a pull request

## Changing the Project's Python Dependencies

### To Add a New Dependency

Add the package to the appropriate [`requirements/*.in`](requirements/)
file(s) and then run:

```terminal
make requirements
```

### To Remove a Dependency

Remove the package from the appropriate [`requirements/*.in`](requirements)
file(s) and then run:

```terminal
make requirements
```

### To Upgrade or Downgrade a Dependency

We rely on [Dependabot](https://github.com/dependabot) to keep all our
dependencies up to date by sending automated pull requests to all our repos.
But if you need to upgrade or downgrade a package manually you can do that
locally.

To upgrade a package to the latest version in all `requirements/*.txt` files:

```terminal
make requirements --always-make args='--upgrade-package <FOO>'
```

To upgrade or downgrade a package to a specific version:

```terminal
make requirements --always-make args='--upgrade-package <FOO>==<X.Y.Z>'
```

To upgrade **all** packages to their latest versions:

```terminal
make requirements --always-make args=--upgrade
```
