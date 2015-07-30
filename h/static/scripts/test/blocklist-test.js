describe('parseUrl', function () {
  'use strict';

  var blocklist = require('../blocklist');
  var parseUrl = blocklist.parseUrl;

  it("returns 'http' for the scheme for http:// URLs", function() {
    assert.equal(parseUrl("http://example.com").scheme, "http");
  });

  it("returns 'https' for the scheme for https:// URLs", function() {
    assert.equal(parseUrl("https://example.com").scheme, "https");
  });

  it("returns the host part correctly", function() {
    var parts = parseUrl("https://example.com:23/foo/bar?oh=no#gar");
    assert.equal(parts.host, "example.com");
  });

  it("returns the port part correctly", function() {
    var parts = parseUrl("https://example.com:23/foo/bar?oh=no#gar");
    assert.equal(parts.port, "23");
  });

  it("returns undefined for the port if there isn't one", function() {
    var parts = parseUrl("https://example.com/foo/bar?oh=no#gar");
    assert.equal(parts.port, undefined);
  });

  it("returns the path part correctly", function() {
    var parts = parseUrl("https://example.com:23/foo/bar?oh=no#gar");
    assert.equal(parts.path, "foo/bar");
  });

  it("returns undefined for the path if there isn't one", function() {
    var parts = parseUrl("https://example.com?oh=no#gar");
    assert.equal(parts.path, undefined);
  });

  it("returns the query part correctly", function() {
    var parts = parseUrl("https://example.com:23/foo/bar?oh=no&ooh=ah#gar");
    assert.equal(parts.query, "oh=no&ooh=ah");
  });

  it("returns undefined for the query if there isn't one", function() {
    var parts = parseUrl("https://example.com#gar");
    assert.equal(parts.query, undefined);
  });

  it("returns the anchor part correctly", function() {
    var parts = parseUrl("https://example.com:23/foo/bar?oh=no&ooh=ah#gar");
    assert.equal(parts.anchor, "gar");
  });

  it("returns undefined for the anchor if there isn't one", function() {
    var parts = parseUrl("https://example.com:23/foo/bar?oh=no&ooh=ah");
    assert.equal(parts.anchor, undefined);
  });
});
