def csp_protected_view(view, info):
    """
    Add Content-Security-Policy headers to responses.

    By default, a global policy is applied to every view.

    Individual views can opt out of CSP altogether by specifying a view option
    ``csp_insecure_optout=True``. This is not recommended.
    """
    if not info.registry.settings.get("csp.enabled", False):
        return view

    # Views can set ``csp_insecure_optout=True`` in their view options to
    # disable CSP for the view.
    if info.options.get("csp_insecure_optout"):
        return view

    policy = info.registry.settings.get("csp", {})
    clauses = [
        " ".join([directive] + values) for directive, values in sorted(policy.items())
    ]
    header_value = "; ".join(clauses)

    if info.registry.settings.get("csp.report_only", False):
        header_name = "Content-Security-Policy-Report-Only"
    else:
        header_name = "Content-Security-Policy"

    def wrapper_view(context, request):
        resp = view(context, request)
        resp.headers[header_name] = header_value
        return resp

    return wrapper_view


csp_protected_view.options = ("csp_insecure_optout",)


def includeme(config):
    config.add_view_deriver(csp_protected_view)
