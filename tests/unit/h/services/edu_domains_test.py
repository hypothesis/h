import logging
from unittest.mock import sentinel

import pytest

from h.services.edu_domains import (
    LOAD_TIMEOUT,
    EduDomainsService,
    factory,
    load_domains,
)
from h.services.exceptions import ExternalRequestError

URL = "https://api.github.com/repos/hypothesis/edu-domains/contents/domains.csv"
TOKEN = "TOKEN"  # noqa: S105


class TestEduDomainsService:
    def test_it_matches_an_address_in_the_list(self, svc):
        assert svc.is_edu_email("someone@cs.stanford.edu") is True

    def test_it_rejects_an_address_outside_the_list(self, svc):
        assert svc.is_edu_email("someone@gmail.com") is False

    @pytest.fixture
    def svc(self):
        return EduDomainsService(frozenset({"stanford.edu"}))


class TestLoadDomains:
    def test_it_downloads_the_list_from_github(self, http_service):
        domains = load_domains(http_service, url=URL, token=TOKEN)

        http_service.get.assert_called_once_with(
            URL,
            headers={
                "Accept": "application/vnd.github.raw+json",
                "Authorization": "Bearer TOKEN",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=LOAD_TIMEOUT,
        )
        assert domains == frozenset({"stanford.edu"})

    @pytest.mark.parametrize(
        "url,token", [(URL, None), (URL, ""), (None, TOKEN), ("", TOKEN)]
    )
    def test_it_returns_an_empty_list_when_not_configured(
        self, http_service, caplog, url, token
    ):
        caplog.set_level(logging.INFO)

        assert load_domains(http_service, url=url, token=token) == frozenset()
        http_service.get.assert_not_called()
        # Not an error: it's how h runs in a clone of the repo.
        assert [record.levelno for record in caplog.records] == [logging.INFO]

    @pytest.mark.parametrize(
        "error",
        [
            # A failed request: GitHub down, a timeout, a revoked token's 401.
            ExternalRequestError(),
            # Anything else: none of it may stop h from starting.
            RuntimeError("unexpected"),
        ],
    )
    def test_it_returns_an_empty_list_if_the_download_fails(
        self, http_service, caplog, error
    ):
        http_service.get.side_effect = error

        assert load_domains(http_service, url=URL, token=TOKEN) == frozenset()
        assert "Couldn't load the list of EDU domains" in caplog.text

    def test_it_skips_and_reports_malformed_entries(self, http_service, caplog):
        http_service.get.return_value.text = "domain\nstanford.edu\n*.ox.ac.uk\n"

        assert load_domains(http_service, url=URL, token=TOKEN) == frozenset(
            {"stanford.edu"}
        )
        assert "Skipped 1 malformed entries" in caplog.text
        assert "*.ox.ac.uk" in caplog.text

    def test_it_reports_an_empty_list(self, http_service, caplog):
        http_service.get.return_value.text = "# Only comments\ndomain\n"

        assert load_domains(http_service, url=URL, token=TOKEN) == frozenset()
        assert "The list of EDU domains is empty" in caplog.text

    @pytest.fixture
    def http_service(self, http_service):
        http_service.get.return_value.text = "# A comment\ndomain\nstanford.edu\n"
        return http_service


class TestFactory:
    def test_it(self, HTTPService, load_domains):
        svc = factory(
            {
                "h.edu_domains_url": sentinel.url,
                "h.edu_domains_github_token": sentinel.token,
            }
        )

        load_domains.assert_called_once_with(
            HTTPService.return_value, url=sentinel.url, token=sentinel.token
        )
        assert svc._domains == load_domains.return_value  # noqa: SLF001

    def test_it_starts_without_any_settings(self, HTTPService):
        # What a clone of the repo does: no URL or token in the settings at all.
        svc = factory({})

        assert svc.is_edu_email("someone@stanford.edu") is False
        HTTPService.return_value.get.assert_not_called()

    @pytest.fixture
    def HTTPService(self, patch):
        return patch("h.services.edu_domains.HTTPService")

    @pytest.fixture
    def load_domains(self, patch):
        return patch("h.services.edu_domains.load_domains")
