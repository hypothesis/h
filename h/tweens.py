# -*- coding: utf-8 -*-

import collections
import logging
import sys
from pyramid import httpexceptions
from pyramid.util import DottedNameResolver

log = logging.getLogger(__name__)
resolver = DottedNameResolver(None)


def auth_token(handler, registry):
    """
    A tween that copies the value of the Annotator token header into the the
    HTTP Authorization header with the Bearer token type.
    """

    def tween(request):
        token = request.headers.get('X-Annotator-Auth-Token')
        if token is not None:
            request.authorization = ('Bearer', token)
        return handler(request)

    return tween


def conditional_http_tween_factory(handler, registry):
    """A tween that sets up conditional response handling for some requests."""
    def conditional_http_tween(request):
        response = handler(request)

        # If the Last-Modified header has been set, we want to enable the
        # conditional response processing.
        if response.last_modified is not None:
            response.conditional_response = True

        # We want to only enable the conditional machinery if either we were
        # given an explicit ETag header by the view...
        if response.etag is not None:
            response.conditional_response = True
            return response

        # ...or we have a buffered response and can generate the ETag header
        # ourself. We only do this for GET or HEAD requests that result in a
        # status code of 200. The subtleties of doing it correctly in other
        # cases don't bear thinking about (at the moment).
        have_buffered_response = (isinstance(response.app_iter,
                                             collections.Sequence) and
                                  len(response.app_iter) == 1)
        cacheable = (request.method in {"GET", "HEAD"} and
                     response.status_code == 200)
        if have_buffered_response and cacheable:
            response.conditional_response = True
            response.md5_etag()

        return response
    return conditional_http_tween


def csrf_tween_factory(handler, registry):
    """A tween that sets a 'XSRF-TOKEN' cookie."""

    def csrf_tween(request):
        response = handler(request)

        # NB: the session does not necessarily supply __len__.
        session_is_empty = len(request.session.keys()) == 0

        # Ignore an empty session.
        if request.session.new and session_is_empty:
            return response

        csrft = request.session.get_csrf_token()

        if request.cookies.get('XSRF-TOKEN') != csrft:
            response.set_cookie('XSRF-TOKEN', csrft)

        return response

    return csrf_tween


def content_security_policy_tween_factory(handler, registry):
    if not registry.settings.get('csp.enabled', False):
        return handler

    policy = registry.settings.get('csp', {})
    policy = "; ".join([
        " ".join([k] + [v2 for v2 in v if v2 is not None])
        for k, v in sorted(policy.items())
        if [v2 for v2 in v if v2 is not None]
    ])

    if registry.settings.get('csp.report_only', False):
        header_name = 'Content-Security-Policy-Report-Only'
    else:
        header_name = 'Content-Security-Policy'

    def content_security_policy_tween(request):
        resp = handler(request)
        resp.headers[header_name] = policy.format(request=request)
        return resp

    return content_security_policy_tween


REDIRECTS = [
    ('/profile/notifications', 'account_notifications'),
    ('/profile/developer', 'account_developer'),
    ('/profile', 'account'),
    ('/register', 'signup'),
    ('/forgot_password', 'forgot_password'),
    ('/reset_password', 'account_reset'),
]


def redirect_tween_factory(handler, registry, redirects=REDIRECTS):
    def redirect_tween(request):
        for old_path, route_name in redirects:
            if request.path.startswith(old_path):
                url = request.route_url(route_name)
                suffix = request.path.replace(old_path, '', 1)
                return httpexceptions.HTTPMovedPermanently(location=(url + suffix))
        return handler(request)

    return redirect_tween


def debug_tm_tween_factory(handler, registry):
    old_commit_veto = registry.settings.get('pyramid_tm.commit_veto', None)
    commit_veto = registry.settings.get('tm.commit_veto', old_commit_veto)
    activate = registry.settings.get('tm.activate_hook')
    commit_veto = resolver.maybe_resolve(commit_veto) if commit_veto else None

    def debug_tm_tween(request):
        if 'repoze.tm.active' in request.environ:
            log.info('repoze.tm.active in request.environ: would skip tm (%s)', request.path)

        if activate is not None:
            if not activate(request):
                log.info('activate hook would skip tm (%s)', request.path)

        manager = request.tm

        try:
            response = handler(request)
            if getattr(request, '_debug_tm', None) is None:
                return response
            if manager.isDoomed():
                log.info('transaction manager explicitly doomed')
            elif commit_veto is not None:
                veto = commit_veto(request, response)
                if veto:
                    log.info('commit veto would trigger abort')
            else:
                log.info('would commit normally')
        except:
            if getattr(request, '_debug_tm', None) is None:
                raise
            exc_info = sys.exc_info()
            try:
                retryable = manager._retryable(*exc_info[:-1])
                if retryable:
                    log.exception('caught retryable exception')
                else:
                    log.exception('caught non-retryable exception')
                raise
            finally:
                del exc_info  # avoid leak

        return response

    return debug_tm_tween
