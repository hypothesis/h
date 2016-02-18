'use strict';

var documentTitle = require('../document-title');

describe('documentTitle', function() {

  it('returns the title linked if the document has title and uri', function() {
    var title = documentTitle({
      title: 'title',
      uri: 'http://example.com/example.html'
    });

    assert(title === 'on &ldquo;<a target="_blank" ' +
                     'href="http://example.com/example.html">' +
                     'title</a>&rdquo;');
  });

  it('returns the title linked if the document has an https uri', function() {
    var title = documentTitle({
      title: 'title',
      uri: 'https://example.com/example.html'
    });

    assert(title === 'on &ldquo;<a target="_blank" '+
                     'href="https://example.com/example.html">' +
                     'title</a>&rdquo;');
  });

  it('returns the title unlinked if doc has title but no uri', function() {
    var title = documentTitle({
      title: 'title',
    });

    assert(title === 'on &ldquo;title&rdquo;');
  });

  it('returns the title unlinked if doc has non-http uri', function() {
    var title = documentTitle({
      title: 'title',
      uri: 'file:///home/bob/Documents/example.pdf'
    });

    assert(title === 'on &ldquo;title&rdquo;');
  });

  it('returns an empty string if the document has no title', function() {
    var title = documentTitle({
      uri: 'http://example.com/example.html'
    });

    assert(title === '');
  });

  it('escapes HTML in the document title', function() {
    var spamLink = '<a href="http://example.com/rubies">Buy rubies!!!</a>';

    var title = documentTitle({
      title: '</a>' + spamLink,
      uri: 'http://example.com/example.html'
    });

    assert(title.indexOf(spamLink) === -1);
  });

  it('escapes HTML in the document URI', function() {
    var spamLink = '<a href="http://example.com/rubies">Buy rubies!!!</a>';

    var title = documentTitle({
      uri: 'http://</a>' + spamLink,
      title: 'title'
    });

    assert(title.indexOf(spamLink) === -1);
  });
});
