__all__ = ["close_db_session_tween_factory"]


def close_db_session_tween_factory(handler, _registry):
    """Return the close_db_session_tween."""

    def close_db_session_tween(request):
        """
        Close the sqlalchemy session.

        This tween runs late in the websocket app's Pyramid request processing
        cycle and makes sure that any DB connections that were opened during
        the request get closed.
        """
        try:
            return handler(request)
        finally:
            request.db.close()

    return close_db_session_tween
