# -*- coding: utf-8 -*-

from __future__ import unicode_literals


class DocumentSearchIndexPresenter(object):
    def __init__(self, document):
        self.document = document

    def asdict(self):
        if not self.document:
            return {}

        d = {}
        if self.document.title:
            d["title"] = [self.document.title]

        if self.document.web_uri:
            d["web_uri"] = self.document.web_uri

        return d
