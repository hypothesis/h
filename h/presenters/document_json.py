# -*- coding: utf-8 -*-

from __future__ import unicode_literals


class DocumentJSONPresenter(object):
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
