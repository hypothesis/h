def is_api_request(request) -> bool:
    """Return True if `request` is an API request."""
    return bool(request.matched_route and request.matched_route.name.startswith("api."))
