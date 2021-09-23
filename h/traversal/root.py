class RootFactory:
    """Base class for all root resource factories."""

    def __init__(self, request):
        self.request = request
