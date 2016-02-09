var uriInfo = require('../lib/uri-info');
var settings = require('./settings.json');

var toResult = require('../../../static/scripts/test/promise-util').toResult;

describe('UriInfo.query', function() {
  var badgeURL = settings.apiUrl + '/badge';

  beforeEach(function() {
    sinon.stub(window, 'fetch').returns(
      Promise.resolve(
        new window.Response('{"total": 1}', {
          status: 200,
          headers: {}
        })
      )
    );

    sinon.stub(console, 'error');
  });

  afterEach(function() {
    window.fetch.restore();
    console.error.restore();
  });

  it('sends the correct XMLHttpRequest', function() {
    return uriInfo.query('tabUrl').then(function () {
      assert.equal(fetch.callCount, 1);
      assert.deepEqual(fetch.lastCall.args, [badgeURL + "?uri=tabUrl"]);
    });
  });

  it('urlencodes the URL appropriately', function() {
    return toResult(uriInfo.query("http://foo.com?bar=baz qüx"))
      .then(function () {
      assert.equal(fetch.callCount, 1);
      assert.deepEqual(fetch.lastCall.args, [badgeURL + "?uri=http%3A%2F%2Ffoo.com%3Fbar%3Dbaz+q%C3%BCx"]);
    });
  });

  var INVALID_RESPONSES = [
    [200, {}, 'this is not valid json'],
    [200, {}, '{"total": "not a valid number"}'],
    [200, {}, '{"rows": []}'],
  ];

  INVALID_RESPONSES.forEach(function (response) {
    it("returns an error if the server's JSON is invalid", function() {
      fetch.returns(
        Promise.resolve(
          new window.Response(
            response[2],
            {status: response[0], headers: response[1]}
          )
        )
      );
      return toResult(uriInfo.query('tabUrl')).then(function (result) {
        assert.ok(result.error);
      });
    });
  });
});
