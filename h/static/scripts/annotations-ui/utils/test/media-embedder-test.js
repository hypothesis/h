import * as mediaEmbedder from '../media-embedder';

describe('sidebar/media-embedder', () => {
  function domElement(html) {
    const element = document.createElement('div');
    element.innerHTML = html;
    return element;
  }

  let clock;

  beforeEach(() => {
    clock = sinon.useFakeTimers();
  });

  afterEach(() => {
    clock.restore();
  });

  /**
   * Find all the media embed elements in a container.
   */
  function findEmbeds(element) {
    return [...element.querySelectorAll('iframe,audio')];
  }

  /**
   * Return the URL of the single media embed in `element`.
   */
  function embedUrl(element) {
    const embeds = findEmbeds(element);
    assert.equal(embeds.length, 1);
    return embeds[0].src;
  }

  function assertStyle(element, expectedProperties) {
    Object.entries(expectedProperties).forEach(([prop, value]) => {
      assert.equal(element.style[prop], value);
    });
  }

  it('replaces YouTube watch links with iframes', () => {
    const urls = [
      'https://www.youtube.com/watch?v=QCkm0lL-6lc',
      'https://www.youtube.com/watch/?v=QCkm0lL-6lc',
      'https://www.youtube.com/watch?foo=bar&v=QCkm0lL-6lc',
      'https://www.youtube.com/watch?foo=bar&v=QCkm0lL-6lc&h=j',
      'https://www.youtube.com/watch?v=QCkm0lL-6lc&foo=bar',
    ];
    urls.forEach(url => {
      const element = domElement('<a href="' + url + '">' + url + '</a>');

      mediaEmbedder.replaceLinksWithEmbeds(element);

      assert.equal(
        embedUrl(element),
        'https://www.youtube.com/embed/QCkm0lL-6lc',
      );
    });
  });

  it('allows whitelisted parameters in YouTube watch URLs', () => {
    const urls = [
      'https://www.youtube.com/watch?v=QCkm0lL-6lc&start=5&end=10',
      'https://www.youtube.com/watch?v=QCkm0lL-6lc&end=10&start=5',
      'https://www.youtube.com/watch/?v=QCkm0lL-6lc&end=10&start=5',
    ];
    urls.forEach(url => {
      const element = domElement('<a href="' + url + '">' + url + '</a>');

      mediaEmbedder.replaceLinksWithEmbeds(element);

      assert.equal(
        embedUrl(element),
        'https://www.youtube.com/embed/QCkm0lL-6lc?end=10&start=5',
      );
    });
  });

  it('translates YouTube watch `t` param to `start` for embed', () => {
    const urls = [
      'https://www.youtube.com/watch?v=QCkm0lL-6lc&t=5&end=10',
      'https://www.youtube.com/watch?v=QCkm0lL-6lc&end=10&t=5',
      'https://www.youtube.com/watch/?v=QCkm0lL-6lc&end=10&t=5',
    ];
    urls.forEach(url => {
      const element = domElement('<a href="' + url + '">' + url + '</a>');

      mediaEmbedder.replaceLinksWithEmbeds(element);

      assert.equal(
        embedUrl(element),
        'https://www.youtube.com/embed/QCkm0lL-6lc?end=10&start=5',
      );
    });
  });

  it('parses YouTube `t` param values into seconds', () => {
    const cases = [
      [
        'https://www.youtube.com/watch?v=QCkm0lL-6lc&t=5m',
        'https://www.youtube.com/embed/QCkm0lL-6lc?start=300',
      ],
      [
        'https://www.youtube.com/watch?v=QCkm0lL-6lc&t=1h5m15s',
        'https://www.youtube.com/embed/QCkm0lL-6lc?start=3915',
      ],
      [
        'https://www.youtube.com/watch?v=QCkm0lL-6lc&t=20m10s',
        'https://www.youtube.com/embed/QCkm0lL-6lc?start=1210',
      ],
      [
        'https://www.youtube.com/watch?v=QCkm0lL-6lc&t=h20m10s',
        'https://www.youtube.com/embed/QCkm0lL-6lc?start=1210',
      ],
      [
        'https://www.youtube.com/watch?v=QCkm0lL-6lc&t=1h20s',
        'https://www.youtube.com/embed/QCkm0lL-6lc?start=3620',
      ],
      [
        'https://www.youtube.com/watch?v=QCkm0lL-6lc&t=1h20ss',
        'https://www.youtube.com/embed/QCkm0lL-6lc?start=3620',
      ],
      [
        'https://www.youtube.com/watch/?v=QCkm0lL-6lc&t=5s',
        'https://www.youtube.com/embed/QCkm0lL-6lc?start=5',
      ],
      [
        'https://www.youtube.com/watch/?v=QCkm0lL-6lc&t=0m5s',
        'https://www.youtube.com/embed/QCkm0lL-6lc?start=5',
      ],
      [
        'https://www.youtube.com/watch/?v=QCkm0lL-6lc&t=m5s',
        'https://www.youtube.com/embed/QCkm0lL-6lc?start=5',
      ],
      [
        'https://www.youtube.com/watch/?v=QCkm0lL-6lc&t=10',
        'https://www.youtube.com/embed/QCkm0lL-6lc?start=10',
      ],
    ];
    cases.forEach(url => {
      const element = domElement('<a href="' + url[0] + '">' + url[0] + '</a>');

      mediaEmbedder.replaceLinksWithEmbeds(element);

      assert.equal(embedUrl(element), url[1]);
    });
  });

  it('excludes non-whitelisted params in YouTube watch links', () => {
    const urls = [
      'https://www.youtube.com/watch?v=QCkm0lL-6lc&start=5&end=10&baz=dingdong',
      'https://www.youtube.com/watch/?v=QCkm0lL-6lc&autoplay=1&end=10&start=5',
    ];
    urls.forEach(url => {
      const element = domElement('<a href="' + url + '">' + url + '</a>');

      mediaEmbedder.replaceLinksWithEmbeds(element);

      assert.equal(
        embedUrl(element),
        'https://www.youtube.com/embed/QCkm0lL-6lc?end=10&start=5',
      );
    });
  });

  it('replaces YouTube share links with iframes', () => {
    const urls = [
      'https://youtu.be/QCkm0lL-6lc',
      'https://youtu.be/QCkm0lL-6lc/',
    ];
    urls.forEach(url => {
      const element = domElement('<a href="' + url + '">' + url + '</a>');

      mediaEmbedder.replaceLinksWithEmbeds(element);

      assert.equal(
        embedUrl(element),
        'https://www.youtube.com/embed/QCkm0lL-6lc',
      );
    });
  });

  it('allows whitelisted parameters in YouTube share links', () => {
    const urls = [
      'https://youtu.be/QCkm0lL-6lc?start=5&end=10',
      'https://youtu.be/QCkm0lL-6lc/?end=10&start=5',
    ];
    urls.forEach(url => {
      const element = domElement('<a href="' + url + '">' + url + '</a>');

      mediaEmbedder.replaceLinksWithEmbeds(element);

      assert.equal(
        embedUrl(element),
        'https://www.youtube.com/embed/QCkm0lL-6lc?end=10&start=5',
      );
    });
  });

  it('translates YouTube share URL `t` param to `start` for embed', () => {
    const urls = [
      'https://youtu.be/QCkm0lL-6lc?t=5&end=10',
      'https://youtu.be/QCkm0lL-6lc/?end=10&t=5',
    ];
    urls.forEach(url => {
      const element = domElement('<a href="' + url + '">' + url + '</a>');

      mediaEmbedder.replaceLinksWithEmbeds(element);

      assert.equal(
        embedUrl(element),
        'https://www.youtube.com/embed/QCkm0lL-6lc?end=10&start=5',
      );
    });
  });

  it('excludes non-whitelisted params in YouTube share links', () => {
    const urls = [
      'https://youtu.be/QCkm0lL-6lc?foo=bar&t=5&end=10&baz=dingdong',
      'https://youtu.be/QCkm0lL-6lc/?autoplay=1&end=10&t=5',
    ];
    urls.forEach(url => {
      const element = domElement('<a href="' + url + '">' + url + '</a>');

      mediaEmbedder.replaceLinksWithEmbeds(element);

      assert.equal(
        embedUrl(element),
        'https://www.youtube.com/embed/QCkm0lL-6lc?end=10&start=5',
      );
    });
  });

  it('replaces Vimeo links with iframes', () => {
    const urls = [
      'https://vimeo.com/149000090',
      'https://vimeo.com/149000090/',
      'https://vimeo.com/149000090#fragment',
      'https://vimeo.com/149000090/#fragment',
      'https://vimeo.com/149000090?foo=bar&a=b',
      'https://vimeo.com/149000090/?foo=bar&a=b',
    ];
    urls.forEach(url => {
      const element = domElement('<a href="' + url + '">' + url + '</a>');

      mediaEmbedder.replaceLinksWithEmbeds(element);

      assert.equal(
        embedUrl(element),
        'https://player.vimeo.com/video/149000090',
      );
    });
  });

  it('replaces Vimeo channel links with iframes', () => {
    const urls = [
      'https://vimeo.com/channels/staffpicks/148845534',
      'https://vimeo.com/channels/staffpicks/148845534/',
      'https://vimeo.com/channels/staffpicks/148845534/?q=foo&id=bar',
      'https://vimeo.com/channels/staffpicks/148845534#fragment',
      'https://vimeo.com/channels/staffpicks/148845534/#fragment',
      'https://vimeo.com/channels/staffpicks/148845534?foo=bar&id=1',
      'https://vimeo.com/channels/otherchannel/148845534',
    ];
    urls.forEach(url => {
      const element = domElement('<a href="' + url + '">' + url + '</a>');

      mediaEmbedder.replaceLinksWithEmbeds(element);

      assert.equal(
        embedUrl(element),
        'https://player.vimeo.com/video/148845534',
      );
    });
  });

  it('replaces internet archive links with iframes', () => {
    const urls = [
      // Video details page.
      'https://archive.org/details/PATH',
      'https://archive.org/details/PATH?start=360&end=420.3',
      'https://archive.org/details/PATH?start=360&end=420.3&unknownparam=1',

      // TV News Archive video details page.
      'https://archive.org/details/PATH/start/360/end/420.3',
      'https://archive.org/details/PATH/start/360/end/420.3?q=ignoreme',

      // Embed link generated by the "Share" links on the details pages.
      'https://archive.org/embed/PATH?start=360&end=420.3',
    ];
    urls.forEach(url => {
      const element = domElement('<a href="' + url + '">' + url + '</a>');

      mediaEmbedder.replaceLinksWithEmbeds(element);

      const actual = embedUrl(element);
      const expected =
        url.indexOf('start') !== -1
          ? 'https://archive.org/embed/PATH?start=360&end=420.3'
          : 'https://archive.org/embed/PATH';
      assert.equal(actual, expected);
    });
  });

  it('replaces audio links with html5 audio elements', () => {
    const urls = [
      'https://archive.org/download/testmp3testfile/mpthreetest.mp3',
      'https://archive.org/download/testmp3testfile/mpthreetest.mp3#fragment',
      'https://archive.org/download/testmp3testfile/mpthreetest.mp3?foo=bar&id=1',
      'http://www.music.helsinki.fi/tmt/opetus/uusmedia/esim/a2002011001-e02.wav',
      'http://www.music.helsinki.fi/tmt/opetus/uusmedia/esim/a2002011001-e02.wav#fragment',
      'http://www.music.helsinki.fi/tmt/opetus/uusmedia/esim/a2002011001-e02.wav?foo=bar&id=4',
      'https://www.w3schools.com/html/horse.ogg',
      'https://www.w3schools.com/html/horse.ogg#fragment',
      'https://www.w3schools.com/html/horse.ogg?foo=bar&id=31',
      'https://wisc.pb.unizin.org/frenchcscr/wp-content/uploads/sites/208/2018/03/6Léry_Conclusion.mp3',
      'https://wisc.pb.unizin.org/frenchcscr/wp-content/uploads/sites/208/2018/03/6L%25C3%25A9ry_Conclusion.mp3',
    ];
    urls.forEach(url => {
      const element = domElement('<a href="' + url + '">' + url + '</a>');

      mediaEmbedder.replaceLinksWithEmbeds(element);

      let encodedURL;
      if (decodeURI(url) !== url) {
        // Test URL is already percent-encoded.
        encodedURL = url;
      } else {
        // Test URL needs percent-encoding.
        encodedURL = encodeURI(url);
      }

      assert.equal(element.childElementCount, 1);
      assert.equal(element.children[0].tagName, 'AUDIO');
      assert.equal(element.children[0].src, encodedURL);
    });
  });

  it('does not replace links if the link text is different', () => {
    const url = 'https://youtu.be/QCkm0lL-6lc';
    const element = domElement('<a href="' + url + '">different label</a>');

    mediaEmbedder.replaceLinksWithEmbeds(element);

    assert.equal(element.childElementCount, 1);
    assert.equal(element.children[0].tagName, 'A');
  });

  [
    {
      href: 'https://youtu.be/abcd',
      // URL that cannot be percent-encoded. Taken from MDN `encodeURI` docs.
      text: 'https://youtu.be/abcd\uD800',
    },
    {
      // URL that cannot be percent-decoded. Taken from MDN `decodeURI` docs.
      href: 'https://youtu.be/abcd/%E0%A4%A',
      text: 'https://youtu.be/abcd',
    },
  ].forEach(({ href, text }) => {
    it('does not replace links if percent-encoding agnostic comparison of href and text fails', () => {
      const element = domElement(`<a href="${href}">${text}</a>`);

      mediaEmbedder.replaceLinksWithEmbeds(element);

      assert.equal(element.childElementCount, 1);
      assert.equal(element.children[0].tagName, 'A');
    });
  });

  it('does not replace non-media links', () => {
    const url = 'https://example.com/example.html';
    const element = domElement('<a href="' + url + '">' + url + '</a>');

    mediaEmbedder.replaceLinksWithEmbeds(element);

    assert.equal(element.childElementCount, 1);
    assert.equal(element.children[0].tagName, 'A');
  });

  it('does not mess with the rest of the HTML', () => {
    const url = 'https://www.youtube.com/watch?v=QCkm0lL-6lc';
    const element = domElement(
      '<p>Look at this video:</p>\n\n' +
        '<a href="' +
        url +
        '">' +
        url +
        '</a>\n\n' +
        "<p>Isn't it cool!</p>\n\n",
    );

    mediaEmbedder.replaceLinksWithEmbeds(element);

    assert.equal(element.childElementCount, 3);
    assert.equal(element.children[0].outerHTML, '<p>Look at this video:</p>');
    assert.equal(element.children[2].outerHTML, "<p>Isn't it cool!</p>");
  });

  it('replaces multiple links with multiple embeds', () => {
    const url1 = 'https://www.youtube.com/watch?v=QCkm0lL-6lc';
    const url2 = 'https://youtu.be/abcdefg';
    const element = domElement(
      '<a href="' +
        url1 +
        '">' +
        url1 +
        '</a>\n\n' +
        '<a href="' +
        url2 +
        '">' +
        url2 +
        '</a>',
    );

    mediaEmbedder.replaceLinksWithEmbeds(element);

    const embeds = findEmbeds(element);

    assert.equal(embeds.length, 2);
    assert.equal(embeds[0].src, 'https://www.youtube.com/embed/QCkm0lL-6lc');
    assert.equal(embeds[1].src, 'https://www.youtube.com/embed/abcdefg');
  });

  it('applies `className` option to video embeds', () => {
    const url = 'https://www.youtube.com/watch?v=QCkm0lL-6lc';
    const element = domElement('<a href="' + url + '">' + url + '</a>');

    mediaEmbedder.replaceLinksWithEmbeds(element, {
      className: 'widget__video',
    });

    assert.equal(element.childElementCount, 1);
    assert.equal(element.children[0].className, 'widget__video');
  });

  it('sets a default width on video embeds if no `className` if provided', () => {
    const url = 'https://www.youtube.com/watch?v=QCkm0lL-6lc';
    const element = domElement('<a href="' + url + '">' + url + '</a>');

    mediaEmbedder.replaceLinksWithEmbeds(element);

    assert.equal(element.childElementCount, 1);
    assert.equal(element.children[0].style.width, '350px');
  });

  it('wraps video embeds in an aspect-ratio box', () => {
    const url = 'https://www.youtube.com/watch?v=QCkm0lL-6lc';
    const element = domElement('<a href="' + url + '">' + url + '</a>');

    mediaEmbedder.replaceLinksWithEmbeds(element);

    assert.equal(element.childElementCount, 1);
    assert.equal(element.children[0].tagName, 'DIV');

    const aspectRatioBox = element.children[0];
    assertStyle(aspectRatioBox, {
      position: 'relative',
      paddingBottom: '56.25%' /* 9/16 as a percentage */,
    });
    assert.equal(aspectRatioBox.childElementCount, 1);

    const embed = aspectRatioBox.children[0];
    assert.equal(embed.tagName, 'IFRAME');
    assertStyle(embed, {
      position: 'absolute',
      top: '0px',
      left: '0px',
      width: '100%',
      height: '100%',
    });
  });
});
