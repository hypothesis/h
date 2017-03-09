# -*- coding: utf-8 -*-

from __future__ import unicode_literals


def csp_protected_view(view, info):
    """
    A view deriver which adds Content-Security-Policy headers to responses.

    By default, a global policy is applied to every view.
    """
    if not info.registry.settings.get('csp.enabled', False):
        return view

    policy = info.registry.settings.get('csp', {})
    policy = "; ".join([
        " ".join([k] + [v2 for v2 in v if v2 is not None])
        for k, v in sorted(policy.items())
        if [v2 for v2 in v if v2 is not None]
    ])

    if info.registry.settings.get('csp.report_only', False):
        header_name = 'Content-Security-Policy-Report-Only'
    else:
        header_name = 'Content-Security-Policy'

    def wrapper_view(context, request):
        resp = view(context, request)
        resp.headers[header_name] = policy.format(request=request)
        return resp
    return wrapper_view


def includeme(config):
    config.add_view_deriver(csp_protected_view)
