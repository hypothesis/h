class DocumentSearchIndexPresenter:
    def __init__(self, document):
        self.document = document

    def asdict(self):
        if not self.document:
            return {}

        document_dict = {}
        if self.document.title:
            document_dict["title"] = [self.document.title]

        if self.document.web_uri:
            document_dict["web_uri"] = self.document.web_uri

        return document_dict


def format_document(document):
    if not document:
        return {}

    document_dict = {}
    if document.title:
        document_dict["title"] = [document.title]

    if document.web_uri:
        document_dict["web_uri"] = document.web_uri

    return document_dict
