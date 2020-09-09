class DocumentJSONPresenter:
    def __init__(self, document):
        self.document = document

    def asdict(self):
        if not self.document:
            return {}

        d = {}
        title = self.document.title
        if title:
            d["title"] = [title]

        return d
