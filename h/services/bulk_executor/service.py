from h.services.bulk_executor.executors import AuthorityCheckingExecutor


class BulkExecutorService:
    """Constructs executors for the Bulk API view."""

    def __init__(self, context, request):
        self.db = request.db

    def get_executor(self):
        """Get an Executor for carrying out bulk actions."""
        return AuthorityCheckingExecutor(self.db)
