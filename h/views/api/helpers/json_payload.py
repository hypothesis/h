from h.views.api.exceptions import PayloadError


def json_payload(request):
    """
    Return the parsed JSON payload from `request`.

    :raise PayloadError: if the request has no valid JSON body
    """
    try:
        return request.json_body
    except ValueError as err:
        raise PayloadError() from err  # noqa: RSE102
