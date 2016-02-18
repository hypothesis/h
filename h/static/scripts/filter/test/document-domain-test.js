'use strict';

var documentDomain = require('../document-domain');

describe('documentDomain', function() {

  it('returns the domain in braces', function() {
    var domain = documentDomain({
      domain: 'example.com'
    });

    assert(domain === '(example.com)');
  });

  it('returns an empty string if domain and title are the same', function() {
    var domain = documentDomain({
      domain: 'example.com',
      title: 'example.com'
    });

    assert(domain === '');
  });

  it('returns an empty string if the document has no domain', function() {
    var domain = documentDomain({
      title: 'example.com'
    });

    assert(domain === '');
  });

  it('returns the filename for local documents with titles', function() {
    var domain = documentDomain({
      title: 'example.com',
      uri: 'file:///home/seanh/MyFile.pdf'
    });

    assert(domain === '(MyFile.pdf)');
  });

  it('replaces %20 with " "', function() {
    var domain = documentDomain({
      title: 'example.com',
      uri: 'file:///home/seanh/My%20File.pdf'
    });

    assert(domain === '(My File.pdf)');
  });

  it('escapes HTML in the document domain', function() {
    var spamLink = '<a href="http://example.com/rubies">Buy rubies!!!</a>';

    var domain = documentDomain({
      title: 'title',
      domain: '</a>' + spamLink
    });

    assert(domain.indexOf(spamLink) === -1);
  });

  it('escapes HTML in the document uri', function() {
    var spamLink = '<a href="http://example.com/rubies">Buy rubies!!!</a>';

    var domain = documentDomain({
      title: 'title',
      uri: 'file:///home/seanh/' + spamLink
    });

    assert(domain.indexOf(spamLink) === -1);
  });
});
