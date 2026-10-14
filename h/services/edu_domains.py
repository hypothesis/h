import logging

from h.services.http import HTTPService
from h.util.edu_domains import is_edu_email, parse_domains

log = logging.getLogger(__name__)


class EduDomainsService:
    """Tell whether an email address belongs to an educational institution."""

    def __init__(self, domains: frozenset[str]) -> None:
        self._domains = domains

    def is_edu_email(self, email: str | None) -> bool:
        """Return True if `email` belongs to a known educational institution."""
        return is_edu_email(email, self._domains)


def factory(settings: dict) -> EduDomainsService:
    """
    Return the process-wide EduDomainsService, with the list already loaded.

    Unlike most service factories this is called once, at configuration time,
    rather than once per request: the list is loaded when the process starts and
    kept for as long as it runs. It is static and rarely changes, and every push
    to main redeploys h, which picks up a new one.
    """
    return EduDomainsService(
        domains=load_domains(
            HTTPService(),
            url=settings.get("h.edu_domains_url"),
            token=settings.get("h.edu_domains_github_token"),
        )
    )


def load_domains(
    http_service: HTTPService, url: str | None, token: str | None
) -> frozenset[str]:
    """
    Download the reference list of educational domains from GitHub.

    The list lives in the private hypothesis/edu-domains repo rather than here,
    because h and its Docker image are both public.

    This never raises. An empty list matches nobody, which turns the EDU role
    survey off, and that is the right outcome for every failure here: h has to
    start without the list -- in a clone of this repo, in an environment that
    isn't configured yet, during a GitHub outage -- rather than refuse to serve
    anything for the sake of a survey.
    """
    # Not an error: it's how h runs everywhere the token isn't configured,
    # including every clone of this repo.
    if not (url and token):
        log.info("No EDU domains token configured, the EDU role survey is off")
        return frozenset()

    try:
        response = http_service.get(
            url,
            headers={
                "Accept": "application/vnd.github.raw+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=LOAD_TIMEOUT,
        )
        domains, malformed = parse_domains(response.text)
    # Anything at all, not just a failed request: this runs while h starts, and
    # nothing about the survey is worth failing that for.
    except Exception:
        log.exception("Couldn't load the list of EDU domains")
        return frozenset()

    if malformed:
        log.error(
            "Skipped %d malformed entries in the list of EDU domains: %s",
            len(malformed),
            malformed[:10],
        )

    if not domains:
        log.error("The list of EDU domains is empty")

    return domains


#: Seconds to wait for GitHub when connecting, and again for each read.
LOAD_TIMEOUT = 10
