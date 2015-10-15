'use strict';

var proxyquire = require('proxyquire');

describe('uriInfo', function() {
  var server;
  var uri = 'http://example.com/example';
  var uriInfo;
  var serviceUrl = 'http://hypothes.is';

  beforeEach(function() {
    server = sinon.fakeServer.create({
      autoRespond: true,
      respondImmediately: true
    });

    sinon.stub(console, 'error');

    var settingsPromise = Promise.resolve({serviceUrl: serviceUrl});
    settingsPromise['@noCallThru'] = true;
    uriInfo = proxyquire(
      '../lib/uri-info', {'./settings': settingsPromise});
  });

  afterEach(function() {
    server.restore();
    console.error.restore();
  });

  it('sends the correct XMLHttpRequest to the server', function() {
    server.respondWith(
      'GET', serviceUrl + '/app/uriinfo?uri=' + uri,
      [200, {}, '{"total": 3, "blocked": false}']
    );

    return uriInfo.get(uri).then(
      function onResolved() {
        assert(server.requests.length === 1);
        var request = server.requests[0];
        assert(request.method === 'GET');
        assert(request.url === serviceUrl + '/app/uriinfo?uri=' + uri);
      },
      function onRejected() {
        assert(false, 'The promise should not be rejected');
      }
    );
  });

  it("returns a rejected promise if the server's JSON is invalid", function() {
    server.respondWith(
      'GET', serviceUrl + '/app/uriinfo?uri=' + uri,
      [200, {}, 'this is not valid json']
    );

    return uriInfo.get(uri).then(
      function onResolved() {
        assert(false, 'The promise should not be resolved');
      },
      function onRejected(error) {
        assert(error instanceof uriInfo.UriInfoError);
        assert(error.message.indexOf('Received invalid JSON') === 0);
      }
    );
  });

  it("logs an error if the server's JSON is invalid", function() {
    server.respondWith(
      'GET', serviceUrl + '/app/uriinfo?uri=' + uri,
      [200, {}, 'this is not valid json']
    );

    return uriInfo.get(uri).then(
      function onFulfilled() {
        assert(false, 'The promise should not be resolved');
      },
      function onRejected() {
        assert(console.error.called);
      });
  });

  it("returns a rejected promise if server's total is invalid", function() {
    server.respondWith(
      'GET', serviceUrl + '/app/uriinfo?uri=' + uri,
      [200, {}, '{"total": "not a valid number"}']
    );

    return uriInfo.get(uri).then(
      function onResolved() {
        assert(false, 'The promise should not be resolved');
      },
      function onRejected(error) {
        assert(error instanceof uriInfo.UriInfoError);
        assert(error.message.indexOf('Received invalid total') === 0);
      }
    );
  });

  it("logs an error if the server's total is invalid", function() {
    server.respondWith(
      'GET', serviceUrl + '/app/uriinfo?uri=' + uri,
      [200, {}, '{"total": "not a valid number"}']
    );

    return uriInfo.get(uri).then(
      function onFulfilled() {
        assert(false, 'The promise should not be resolved');
      },
      function onRejected() {
        assert(console.error.called);
      });
  });

  it("returns a rejected promise if server response has no total", function() {
    server.respondWith(
      'GET', serviceUrl + '/app/uriinfo?uri=' + uri,
      [200, {}, '{"foo": "bar"}']
    );

    return uriInfo.get(uri).then(
      function onResolved() {
        assert(false, 'The promise should not be resolved');
      },
      function onRejected(error) {
        assert(error instanceof uriInfo.UriInfoError);
        assert(error.message.indexOf('Received invalid total') === 0);
      }
    );
  });

  it("logs an error if the server response has no total", function() {
    server.respondWith(
      'GET', serviceUrl + '/app/uriinfo?uri=' + uri,
      [200, {}, '{"foo": "bar"}']
    );

    return uriInfo.get(uri).then(
      function onFulfilled() {
        assert(false, 'The promise should not be resolved');
      },
      function onRejected() {
        assert(console.error.called);
      });
  });

  it("returns a rejected promise if server's blocked is invalid", function() {
    server.respondWith(
      'GET', serviceUrl + '/app/uriinfo?uri=' + uri,
      [200, {}, '{"total": 3, "blocked": "foo"}']
    );

    return uriInfo.get(uri).then(
      function onResolved() {
        assert(false, 'The promise should not be resolved');
      },
      function onRejected(error) {
        assert(error instanceof uriInfo.UriInfoError);
        assert(error.message.indexOf('Received invalid blocked') === 0);
      }
    );
  });

  it("logs an error if the server's blocked is invalid", function() {
    server.respondWith(
      'GET', serviceUrl + '/app/uriinfo?uri=' + uri,
      [200, {}, '{"total": 3, "blocked": "foo"}']
    );

    return uriInfo.get(uri).then(
      function onFulfilled() {
        assert(false, 'The promise should not be resolved');
      },
      function onRejected() {
        assert(console.error.called);
      });
  });

  it("returns a rejected promise if response has no blocked", function() {
    server.respondWith(
      'GET', serviceUrl + '/app/uriinfo?uri=' + uri,
      [200, {}, '{"total": 3}']
    );

    return uriInfo.get(uri).then(
      function onResolved() {
        assert(false, 'The promise should not be resolved');
      },
      function onRejected(error) {
        assert(error instanceof uriInfo.UriInfoError);
        assert(error.message.indexOf('Received invalid blocked') === 0);
      }
    );
  });

  it("logs an error if the server response has no blocked", function() {
    server.respondWith(
      'GET', serviceUrl + '/app/uriinfo?uri=' + uri,
      [200, {}, '{"total": 3}']
    );

    return uriInfo.get(uri).then(
      function onFulfilled() {
        assert(false, 'The promise should not be resolved');
      },
      function onRejected() {
        assert(console.error.called);
      });
  });

  it('returns a rejected promise if the request fails', function() {
    server.respondWith(
      'GET', serviceUrl + '/app/uriinfo?uri=' + uri,
      [500, {}, '']
    );

    return uriInfo.get(uri).then(
      function onFulfilled() {
        assert(false, 'The promise should not be resolved');
      },
      function onRejected(error) {
        assert(error instanceof uriInfo.UriInfoError);
        assert(error.message.indexOf('Received invalid JSON') === 0);
      });
  });

  it('logs an error if the request fails', function() {
    server.respondWith(
      'GET', serviceUrl + '/app/uriinfo?uri=' + uri,
      [500, {}, '']
    );

    return uriInfo.get(uri).then(
      function onFulfilled() {
        assert(false, 'The promise should not be resolved');
      },
      function onRejected() {
        assert(console.error.called);
      });
  });

  it("doesn't send consecutive requests for the same uri", function() {
    uriInfo.get(uri);
    uriInfo.get(uri);
    assert(server.requests.length === 1);
  });

  it("does send consecutive requests for different uris", function() {
    return Promise.all([
      uriInfo.get('http://example.com/example1'),
      uriInfo.get('http://example.com/example2'),
      uriInfo.get('http://example.com/example1'),
      uriInfo.get('http://example.com/example2')
    ])
    .then(
      function onFulfilled() {
        assert(false, 'The Promise should not be fulfilled');
      },
      function onRejected() {
        assert(server.requests.length === 4);
      }
    );
  });

  it("doesn't send requests if uri is undefined", function() {
    uriInfo.get(undefined);
    assert(server.requests.length === 0);
  });
});
