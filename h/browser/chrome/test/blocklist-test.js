'use strict';

var proxyquire = require('proxyquire');

describe('blocklist', function() {
  var server;
  var uri = 'http://example.com/example';
  var blocklist;
  var serviceUrl = 'http://hypothes.is/api';

  beforeEach(function() {
    server = sinon.fakeServer.create({
      autoRespond: true,
      respondImmediately: true
    });

    sinon.stub(console, 'error');

    var settingsPromise = Promise.resolve({serviceUrl: serviceUrl});
    settingsPromise['@noCallThru'] = true;
    blocklist = proxyquire(
      '../lib/blocklist', {'./settings': settingsPromise});
  });

  afterEach(function() {
    server.restore();
    console.error.restore();
  });

  it('sends the correct XMLHttpRequest to the server', function() {
    server.respondWith(
      'GET', serviceUrl + '/blocklist?uri=' + uri,
      [200, {}, '{"total": 3, "blocked": false}']
    );

    return blocklist(uri).then(
      function onResolved() {
        assert(server.requests.length === 1);
        var request = server.requests[0];
        assert(request.method === 'GET');
        assert(request.url === serviceUrl + '/blocklist?uri=' + uri);
      },
      function onRejected() {
        assert(false, 'The promise should not be rejected');
      }
    );
  });

  it("returns a rejected promise if the server's JSON is invalid", function() {
    server.respondWith(
      'GET', serviceUrl + '/blocklist?uri=' + uri,
      [200, {}, 'this is not valid json']
    );

    return blocklist(uri).then(
      function onResolved() {
        assert(false, 'The promise should not be resolved');
      },
      function onRejected(error) {
        assert(error.reason.indexOf('Received invalid JSON') === 0);
      }
    );
  });

  it("logs an error if the server's JSON is invalid", function() {
    server.respondWith(
      'GET', serviceUrl + '/blocklist?uri=' + uri,
      [200, {}, 'this is not valid json']
    );

    return blocklist(uri).then(
      function onFulfilled() {
        assert(false, 'The promise should not be resolved');
      },
      function onRejected() {
        assert(console.error.called);
      });
  });

  it("returns a rejected promise if server's total is invalid", function() {
    server.respondWith(
      'GET', serviceUrl + '/blocklist?uri=' + uri,
      [200, {}, '{"total": "not a valid number"}']
    );

    return blocklist(uri).then(
      function onResolved() {
        assert(false, 'The promise should not be resolved');
      },
      function onRejected(error) {
        assert(error.reason.indexOf('Received invalid total') === 0);
      }
    );
  });

  it("logs an error if the server's total is invalid", function() {
    server.respondWith(
      'GET', serviceUrl + '/blocklist?uri=' + uri,
      [200, {}, '{"total": "not a valid number"}']
    );

    return blocklist(uri).then(
      function onFulfilled() {
        assert(false, 'The promise should not be resolved');
      },
      function onRejected() {
        assert(console.error.called);
      });
  });

  it("returns a rejected promise if server response has no total", function() {
    server.respondWith(
      'GET', serviceUrl + '/blocklist?uri=' + uri,
      [200, {}, '{"foo": "bar"}']
    );

    return blocklist(uri).then(
      function onResolved() {
        assert(false, 'The promise should not be resolved');
      },
      function onRejected(error) {
        assert(error.reason.indexOf('Received invalid total') === 0);
      }
    );
  });

  it("logs an error if the server response has no total", function() {
    server.respondWith(
      'GET', serviceUrl + '/blocklist?uri=' + uri,
      [200, {}, '{"foo": "bar"}']
    );

    return blocklist(uri).then(
      function onFulfilled() {
        assert(false, 'The promise should not be resolved');
      },
      function onRejected() {
        assert(console.error.called);
      });
  });

  it("returns a rejected promise if server's blocked is invalid", function() {
    server.respondWith(
      'GET', serviceUrl + '/blocklist?uri=' + uri,
      [200, {}, '{"total": 3, "blocked": "foo"}']
    );

    return blocklist(uri).then(
      function onResolved() {
        assert(false, 'The promise should not be resolved');
      },
      function onRejected(error) {
        assert(error.reason.indexOf('Received invalid blocked') === 0);
      }
    );
  });

  it("logs an error if the server's blocked is invalid", function() {
    server.respondWith(
      'GET', serviceUrl + '/blocklist?uri=' + uri,
      [200, {}, '{"total": 3, "blocked": "foo"}']
    );

    return blocklist(uri).then(
      function onFulfilled() {
        assert(false, 'The promise should not be resolved');
      },
      function onRejected() {
        assert(console.error.called);
      });
  });

  it("returns a rejected promise if response has no blocked", function() {
    server.respondWith(
      'GET', serviceUrl + '/blocklist?uri=' + uri,
      [200, {}, '{"total": 3}']
    );

    return blocklist(uri).then(
      function onResolved() {
        assert(false, 'The promise should not be resolved');
      },
      function onRejected(error) {
        assert(error.reason.indexOf('Received invalid blocked') === 0);
      }
    );
  });

  it("logs an error if the server response has no blocked", function() {
    server.respondWith(
      'GET', serviceUrl + '/blocklist?uri=' + uri,
      [200, {}, '{"total": 3}']
    );

    return blocklist(uri).then(
      function onFulfilled() {
        assert(false, 'The promise should not be resolved');
      },
      function onRejected() {
        assert(console.error.called);
      });
  });

  it('returns a rejected promise if the request fails', function() {
    server.respondWith(
      'GET', serviceUrl + '/blocklist?uri=' + uri,
      [500, {}, '']
    );

    return blocklist(uri).then(
      function onFulfilled() {
        assert(false, 'The promise should not be resolved');
      },
      function onRejected(error) {
        assert(error.reason.indexOf('Received invalid JSON') === 0);
      });
  });

  it('logs an error if the request fails', function() {
    server.respondWith(
      'GET', serviceUrl + '/blocklist?uri=' + uri,
      [500, {}, '']
    );

    return blocklist(uri).then(
      function onFulfilled() {
        assert(false, 'The promise should not be resolved');
      },
      function onRejected() {
        assert(console.error.called);
      });
  });

  it("doesn't send consecutive requests for the same url", function() {
    blocklist(uri);
    blocklist(uri);
    assert(server.requests.length === 1);
  });

  it("does send consecutive requests for different urls", function() {
    return Promise.all([
      blocklist('http://example.com/example1'),
      blocklist('http://example.com/example2'),
      blocklist('http://example.com/example1'),
      blocklist('http://example.com/example2')
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

  it("doesn't send requests if url is undefined", function() {
    blocklist(undefined);
    assert(server.requests.length === 0);
  });
});
