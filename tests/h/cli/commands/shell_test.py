# -*- coding: utf-8 -*-

import sys

import mock
import pytest

from h.cli.commands import shell


class TestAutoDetect(object):
    def test_bpython(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "bpython", mock.sentinel.bpython)
        assert shell.autodetect() == "bpython"

    def test_bpython_over_ipython(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "bpython", mock.sentinel.bpython)
        monkeypatch.setitem(sys.modules, "IPython", mock.sentinel.bpython)
        assert shell.autodetect() == "bpython"

    def test_ipython(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "IPython", mock.sentinel.bpython)
        assert shell.autodetect() == "ipython"

    def test_plain(self):
        assert shell.autodetect() == "plain"


@pytest.mark.usefixtures("banner")
class TestShells(object):
    def test_bpython(self, monkeypatch):
        fake_bpython = mock.Mock(spec_set=["embed"])
        monkeypatch.setitem(sys.modules, "bpython", fake_bpython)

        shell.bpython(foo="bar", baz="qux")

        fake_bpython.embed.assert_called_once_with(
            {"foo": "bar", "baz": "qux"}, banner="custom banner!"
        )

    def test_ipython(self, monkeypatch):
        fake_ipython = mock.Mock(spec_set=["start_ipython"])
        monkeypatch.setitem(sys.modules, "IPython", fake_ipython)
        fake_traitlets = mock.Mock(spec_set=["config"])
        fake_traitlets_config = mock.Mock(spec_set=["get_config"])
        monkeypatch.setitem(sys.modules, "traitlets", fake_traitlets)
        monkeypatch.setitem(sys.modules, "traitlets.config", fake_traitlets_config)

        shell.ipython(foo="bar", baz="qux")

        _, kwargs = fake_ipython.start_ipython.call_args

        assert kwargs["argv"] == []
        assert kwargs["user_ns"] == {"foo": "bar", "baz": "qux"}
        assert kwargs["config"].TerminalInteractiveShell.banner2 == "custom banner!"

    def test_plain(self, monkeypatch):
        fake_code = mock.Mock(spec_set=["interact"])
        monkeypatch.setitem(sys.modules, "code", fake_code)

        shell.plain(foo="bar", baz="qux")

        fake_code.interact.assert_called_once_with(
            banner="custom banner!", local={"foo": "bar", "baz": "qux"}
        )

    @pytest.fixture
    def banner(self, monkeypatch):
        monkeypatch.setattr(shell, "BANNER", "custom banner!")


@pytest.mark.usefixtures("code", "models")
class TestShellCommand(object):
    def test_runs_bootstrap(self, cli):
        config = {"bootstrap": mock.Mock(spec_set=[])}

        cli.invoke(shell.shell, obj=config)

        config["bootstrap"].assert_called_once_with()

    def test_can_select_shell_manually(self, cli, monkeypatch):
        config = {"bootstrap": mock.Mock(spec_set=[])}
        fake_bpython = mock.Mock(spec_set=["embed"])
        monkeypatch.setitem(sys.modules, "bpython", fake_bpython)

        cli.invoke(shell.shell, ["--type", "bpython"], obj=config)

        assert fake_bpython.embed.called

    def test_passes_useful_locals(self, cli, code, models):
        bootstrap = mock.Mock(spec_set=[])
        request = bootstrap.return_value
        config = {"bootstrap": bootstrap}

        cli.invoke(shell.shell, obj=config)

        _, kwargs = code.interact.call_args
        locals_ = kwargs["local"]

        assert locals_ == {
            "m": models,
            "models": models,
            "registry": request.registry,
            "request": request,
            "session": request.db,
        }

    def test_error_if_shell_not_found(self, cli):
        config = {"bootstrap": mock.Mock(spec_set=[])}

        result = cli.invoke(shell.shell, ["--type", "bpython"], obj=config)

        assert result.exit_code != 0

    @pytest.fixture
    def code(self, monkeypatch):
        code = mock.Mock(spec_set=["interact"])
        monkeypatch.setitem(sys.modules, "code", code)
        return code

    @pytest.fixture
    def models(self, monkeypatch):
        h = mock.Mock(spec_set=["models"])
        h.models = mock.sentinel.models
        monkeypatch.setitem(sys.modules, "h", h)
        return h.models
