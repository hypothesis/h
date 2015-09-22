'use strict';

var documentDomainFilterProvider = require('../document-domain');

describe('documentDomain', function() {

  it('returns the domain in braces', function() {
    var domain = documentDomainFilterProvider()({
      domain: 'example.com'
    });

    assert(domain === '(example.com)');
  });

  it('returns an empty string if domain and title are the same', function() {
    var domain = documentDomainFilterProvider()({
      domain: 'example.com',
      title: 'example.com'
    });

    assert(domain === '');
  });

  it('returns an empty string if the document has no domain', function() {
    var domain = documentDomainFilterProvider()({
      title: 'example.com'
    });

    assert(domain === '');
  });

  it('escapes HTML in the document domain', function() {
    var spamLink = '<a href="http://example.com/rubies">Buy rubies!!!</a>';

    var domain = documentDomainFilterProvider()({
      title: 'title',
      domain: '</a>' + spamLink
    });

    assert(domain.indexOf(spamLink) === -1);
  });
});
