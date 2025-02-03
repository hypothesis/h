from h.services.html import parse_html_links


def test_parse_html_links():
    html = 'Hello <a data-hyp-mention data-userid="devdata_user">@devdata_user</a>'
    links = parse_html_links(html)
    assert links == [{"data-hyp-mention": None, "data-userid": "devdata_user"}]


def test_parse_html_links_no_links():
    html = "<p>Hello world</p>"
    links = parse_html_links(html)
    assert links == []
