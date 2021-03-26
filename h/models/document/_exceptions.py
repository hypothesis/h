from pyramid_retry import mark_error_retryable


class ConcurrentUpdateError(Exception):
    """Raised when concurrent updates to document data conflict."""


mark_error_retryable(ConcurrentUpdateError)
