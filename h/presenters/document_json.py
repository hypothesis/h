class DocumentJSONPresenter:
    def __init__(self, document):
        self.document = document

    def asdict(self):
        if self.document and (title := self.document.title):
            return {"title": [title]}

        return {}
