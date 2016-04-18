'use strict';

var toResult = require('../../../static/scripts/test/promise-util').toResult;
var unroll = require('../../../static/scripts/test/util').unroll;

var uriInfo = require('../lib/uri-info');
var settings = require('./settings.json');

describe('UriInfo.query', function () {
  var badgeURL = settings.apiUrl + '/badge';

  beforeEach(function () {
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

  afterEach(function () {
    window.fetch.restore();
    console.error.restore();
  });

  it('sends the correct XMLHttpRequest', function () {
    return uriInfo.query('tabUrl').then(function () {
      assert.equal(fetch.callCount, 1);
      assert.deepEqual(
        fetch.lastCall.args,
        [badgeURL + '?uri=tabUrl', {credentials: 'include'}]);
    });
  });

  it('urlencodes the URL appropriately', function () {
    return toResult(uriInfo.query('http://foo.com?bar=baz qüx'))
      .then(function () {
      assert.equal(fetch.callCount, 1);
      assert.equal(
        fetch.lastCall.args[0],
        badgeURL + '?uri=http%3A%2F%2Ffoo.com%3Fbar%3Dbaz+q%C3%BCx');
    });
  });

  var INVALID_RESPONSE_FIXTURES = [
    {status: 200, headers: {}, body: 'this is not valid json'},
    {status: 200, headers: {}, body: '{"total": "not a valid number"}'},
    {status: 200, headers: {}, body: '{"rows": []}'},
  ];

  unroll('returns an error if the server\'s JSON is invalid', function (response) {
    fetch.returns(
      Promise.resolve(
        new window.Response(
          response.body,
          {status: response.status, headers: response.headers}
        )
      )
    );
    return toResult(uriInfo.query('tabUrl')).then(function (result) {
      assert.ok(result.error);
    });
  }, INVALID_RESPONSE_FIXTURES);
});
