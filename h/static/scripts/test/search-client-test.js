'use strict';

var SearchClient = require('../search-client');

function await(emitter, event) {
  return new Promise(function (resolve) {
    emitter.on(event, resolve);
  });
}

describe('SearchClient', function () {
  var RESULTS = [
    {id: 'one'},
    {id: 'two'},
    {id: 'three'},
    {id: 'four'},
  ];

  var fakeResource;

  beforeEach(function () {
    fakeResource = {
      get: sinon.spy(function (params) {
        return {
          $promise: Promise.resolve({
            rows: RESULTS.slice(params.offset,
              params.offset + params.limit),
            total: RESULTS.length,
          }),
        };
      }),
    };
  });

  it('emits "results"', function () {
    var client = new SearchClient(fakeResource);
    var onResults = sinon.stub();
    client.on('results', onResults);
    client.get({uri: 'http://example.com'});
    return await(client, 'end').then(function () {
      assert.calledWith(onResults, RESULTS);
    });
  });

  it('emits "results" with chunks in incremental mode', function () {
    var client = new SearchClient(fakeResource, {chunkSize: 2});
    var onResults = sinon.stub();
    client.on('results', onResults);
    client.get({uri: 'http://example.com'});
    return await(client, 'end').then(function () {
      assert.calledWith(onResults, RESULTS.slice(0,2));
      assert.calledWith(onResults, RESULTS.slice(2,4));
    });
  });

  it('emits "results" once in non-incremental mode', function () {
    var client = new SearchClient(fakeResource,
      {chunkSize: 2, incremental: false});
    var onResults = sinon.stub();
    client.on('results', onResults);
    client.get({uri: 'http://example.com'});
    return await(client, 'end').then(function () {
      assert.calledOnce(onResults);
      assert.calledWith(onResults, RESULTS);
    });
  });

  it('does not emit "results" if canceled', function () {
    var client = new SearchClient(fakeResource);
    var onResults = sinon.stub();
    var onEnd = sinon.stub();
    client.on('results', onResults);
    client.on('end', onEnd);
    client.get({uri: 'http://example.com'});
    client.cancel();
    return Promise.resolve().then(function () {
      assert.notCalled(onResults);
      assert.called(onEnd);
    });
  });

  it('emits "error" event if search fails', function () {
    var err = new Error('search failed');
    fakeResource.get = function () {
      return {
        $promise: Promise.reject(err),
      };
    };
    var client = new SearchClient(fakeResource);
    var onError = sinon.stub();
    client.on('error', onError);
    client.get({uri: 'http://example.com'});
    return await(client, 'end').then(function () {
      assert.calledWith(onError, err);
    });
  });
});
