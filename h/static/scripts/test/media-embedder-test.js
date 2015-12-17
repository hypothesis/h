'use strict';

var mediaEmbedder = require('../media-embedder.js');

describe('media-embedder', function () {
  function domElement (html) {
    var element = document.createElement('div');
    element.innerHTML = html;
    return element;
  }

  it('replaces YouTube watch links with iframes', function () {
    var urls = [
      'https://www.youtube.com/watch?v=QCkm0lL-6lc',
      'https://www.youtube.com/watch/?v=QCkm0lL-6lc',
      'https://www.youtube.com/watch?foo=bar&v=QCkm0lL-6lc',
      'https://www.youtube.com/watch?foo=bar&v=QCkm0lL-6lc&h=j',
      'https://www.youtube.com/watch?v=QCkm0lL-6lc&foo=bar',
    ];
    urls.forEach(function (url) {
      var element = domElement('<a href="' + url + '">' + url + '</a>');

      mediaEmbedder.replaceLinksWithEmbeds(element);

      assert.equal(element.childElementCount, 1);
      assert.equal(element.children[0].tagName, 'IFRAME', url);
      assert.equal(
        element.children[0].src,
        'https://www.youtube.com/embed/QCkm0lL-6lc');
    });
  });

  it('replaces YouTube share links with iframes', function () {
    var urls = [
      'https://youtu.be/QCkm0lL-6lc',
      'https://youtu.be/QCkm0lL-6lc/',
    ]
    urls.forEach(function (url) {
      var element = domElement('<a href="' + url + '">' + url + '</a>');

      mediaEmbedder.replaceLinksWithEmbeds(element);

      assert.equal(element.childElementCount, 1);
      assert.equal(element.children[0].tagName, 'IFRAME');
      assert.equal(
        element.children[0].src, 'https://www.youtube.com/embed/QCkm0lL-6lc');
    });
  });

  it('replaces Vimeo links with iframes', function () {
    var urls = [
      'https://vimeo.com/149000090',
      'https://vimeo.com/149000090/',
      'https://vimeo.com/149000090#fragment',
      'https://vimeo.com/149000090/#fragment',
      'https://vimeo.com/149000090?foo=bar&a=b',
      'https://vimeo.com/149000090/?foo=bar&a=b',
    ]
    urls.forEach(function (url) {
      var element = domElement('<a href="' + url + '">' + url + '</a>');

      mediaEmbedder.replaceLinksWithEmbeds(element);

      assert.equal(element.childElementCount, 1);
      assert.equal(element.children[0].tagName, 'IFRAME');
      assert.equal(
        element.children[0].src, 'https://player.vimeo.com/video/149000090');
      });
  });

  it('replaces Vimeo channel links with iframes', function () {
    var urls = [
      'https://vimeo.com/channels/staffpicks/148845534',
      'https://vimeo.com/channels/staffpicks/148845534/',
      'https://vimeo.com/channels/staffpicks/148845534/?q=foo&id=bar',
      'https://vimeo.com/channels/staffpicks/148845534#fragment',
      'https://vimeo.com/channels/staffpicks/148845534/#fragment',
      'https://vimeo.com/channels/staffpicks/148845534?foo=bar&id=1',
      'https://vimeo.com/channels/otherchannel/148845534',
    ];
    urls.forEach(function (url) {
      var element = domElement('<a href="' + url + '">' + url + '</a>');

      mediaEmbedder.replaceLinksWithEmbeds(element);

      assert.equal(element.childElementCount, 1);
      assert.equal(element.children[0].tagName, 'IFRAME');
      assert.equal(
        element.children[0].src, 'https://player.vimeo.com/video/148845534');
    });
  });

  it('does not replace links if the link text is different', function () {
    var url = 'https://youtu.be/QCkm0lL-6lc';
    var element = domElement('<a href="' + url + '">different label</a>');

    mediaEmbedder.replaceLinksWithEmbeds(element);

    assert.equal(element.childElementCount, 1);
    assert.equal(element.children[0].tagName, 'A');
  });

  it('does not replace non-media links', function () {
    var url = 'https://example.com/example.html';
    var element = domElement('<a href="' + url + '">' + url + '</a>');

    mediaEmbedder.replaceLinksWithEmbeds(element);

    assert.equal(element.childElementCount, 1);
    assert.equal(element.children[0].tagName, 'A');
  });

  it('does not mess with the rest of the HTML', function () {
    var url = 'https://www.youtube.com/watch?v=QCkm0lL-6lc';
    var element = domElement(
      '<p>Look at this video:</p>\n\n' +
      '<a href="' + url + '">' + url + '</a>\n\n' +
      '<p>Isn\'t it cool!</p>\n\n');

    mediaEmbedder.replaceLinksWithEmbeds(element);

    assert.equal(element.childElementCount, 3);
    assert.equal(
      element.children[0].outerHTML, '<p>Look at this video:</p>');
    assert.equal(
      element.children[2].outerHTML, '<p>Isn\'t it cool!</p>');
  });

  it('replaces multiple links with multiple embeds', function () {
    var url1 = 'https://www.youtube.com/watch?v=QCkm0lL-6lc';
    var url2 = 'https://youtu.be/abcdefg';
    var element = domElement(
        '<a href="' + url1 + '">' + url1 + '</a>\n\n' +
        '<a href="' + url2 + '">' + url2 + '</a>');

    mediaEmbedder.replaceLinksWithEmbeds(element);

    assert.equal(element.childElementCount, 2);
    assert.equal(element.children[0].tagName, 'IFRAME');
    assert.equal(
      element.children[0].src, 'https://www.youtube.com/embed/QCkm0lL-6lc');
    assert.equal(element.children[1].tagName, 'IFRAME');
    assert.equal(
      element.children[1].src, 'https://www.youtube.com/embed/abcdefg');
  });
});
