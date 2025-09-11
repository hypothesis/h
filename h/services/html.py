from html.parser import HTMLParser


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._links.append(dict(attrs))

    def get_links(self) -> list[dict]:
        return self._links


def parse_html_links(html: str) -> list[dict]:
    parser = LinkParser()
    parser.feed(html)
    return parser.get_links()
