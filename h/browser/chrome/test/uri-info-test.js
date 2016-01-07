var uriInfo = require('../lib/uri-info');
var settings = require('./settings.json');

/**
 * Takes a Promise<T> and returns a Promise<Result>
 * where Result = { result: T } | { error: any }.
 *
 * This is useful for testing that promises are rejected
 * as expected in tests.
 */
function toResult(promise) {
  return promise.then(function (result) {
    return { result: result };
  }).catch(function (err) {
    return { error: err }
  });
}

describe('UriInfo.query', function() {
  var server;
  var badgeURL = settings.apiUrl + '/badge';

  beforeEach(function() {
    server = sinon.fakeServer.create({
      autoRespond: true,
      respondImmediately: true
    });
    server.respondWith(
      "GET", badgeURL + "?uri=tabUrl",
      [200, {}, '{"total": 1}']
    );
    sinon.stub(console, 'error');
  });

  afterEach(function() {
    server.restore();
    console.error.restore();
  });

  it('sends the correct XMLHttpRequest', function() {
    return uriInfo.query('tabUrl').then(function () {
      assert.equal(server.requests.length, 1);
      var request = server.requests[0];
      assert.equal(request.method, "GET");
      assert.equal(request.url, badgeURL + "?uri=tabUrl");
    });
  });

  it('urlencodes the URL appropriately', function() {
    return toResult(uriInfo.query("http://foo.com?bar=baz qüx"))
      .then(function () {
      assert.equal(server.requests.length, 1);
      var request = server.requests[0];
      assert.equal(request.method, "GET");
      assert.equal(request.url, badgeURL + "?uri=http%3A%2F%2Ffoo.com%3Fbar%3Dbaz+q%C3%BCx");
    });
  });

  var INVALID_RESPONSES = [
    [200, {}, 'this is not valid json'],
    [200, {}, '{"total": "not a valid number"}'],
    [200, {}, '{"rows": []}'],
  ];

  INVALID_RESPONSES.forEach(function (response) {
    it("returns an error if the server's JSON is invalid", function() {
      server.respondWith(
        "GET", badgeURL + "?uri=tabUrl",
        response
      );
      return toResult(uriInfo.query('tabUrl')).then(function (result) {
        assert.ok(result.error);
      });
    });
  });
});
