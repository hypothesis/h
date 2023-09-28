class DocumentJSONPresenter:
    def __init__(self, document):
        self.document = document

    def asdict(self):
        if not self.document:
            return {}

        document_dict = {}
        title = self.document.title
        if title:  # pragma: no cover
            document_dict["title"] = [title]

        return document_dict
