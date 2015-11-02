describe('TabState', function () {
  'use strict';

  var TabState = require('../lib/tab-state');
  var states = TabState.states;

  var state;
  var onChange;

  beforeEach(function () {
    onChange = sinon.spy();
    state = new TabState({
      1: {state: states.ACTIVE}
    }, onChange);
  });

  it('can be initialized without any default state', function () {
    assert.doesNotThrow(function () {
      state = new TabState(null, onChange);
      state.isTabActive(1);
    });
  });

  it('can be initialized without an onchange callback', function () {
    assert.doesNotThrow(function () {
      state = new TabState();
      state.isTabActive(1);
    });
  });

  describe('.load', function () {
    it('replaces the current tab states with a new object', function () {
      state.load({2: {state: states.INACTIVE}});
      assert.equal(state.isTabActive(1), false);
      assert.equal(state.isTabInactive(2), true);
    });
  });

  describe('.activateTab', function () {
    it('sets the state for the tab id provided', function () {
      state.activateTab(2);
      assert.equal(state.isTabActive(2), true);
    });

    it('triggers an onchange handler', function () {
      state.activateTab(2);
      assert.calledWith(onChange, 2, sinon.match({state: states.ACTIVE}));
    });
  });

  describe('.deactivateTab', function () {
    it('sets the state for the tab id provided', function () {
      state.deactivateTab(2);
      assert.equal(state.isTabInactive(2), true);
    });

    it('triggers an onchange handler', function () {
      state.deactivateTab(2);
      assert.calledWith(onChange, 2, sinon.match({state: states.INACTIVE}));
    });
  });

  describe('.errorTab', function () {
    it('sets the state for the tab id provided', function () {
      state.errorTab(2);
      assert.equal(state.isTabErrored(2), true);
    });

    it('triggers an onchange handler', function () {
      state.errorTab(2);
      assert.calledWith(onChange, 2, sinon.match({state: states.ERRORED}));
    });
  });

  describe('.clearTab', function () {
    it('removes the state for the tab id provided', function () {
      state.clearTab(1);
      assert.equal(state.isTabActive(1), false), 'expected isTabActive to return false';
      assert.equal(state.isTabInactive(1), true, 'expected isTabInactive to return true');
      assert.equal(state.isTabErrored(1), false, 'expected isTabInactive to return false');
    });

    it('triggers an onchange handler', function () {
      state.clearTab(1);
      assert.calledWith(onChange, 1, undefined);
    });
  });

  describe('.isTabActive', function () {
    it('returns true if the tab is active', function () {
      state.activateTab(1);
      assert.equal(state.isTabActive(1), true);
    });
  });

  describe('.isTabInactive', function () {
    it('returns true if the tab is inactive', function () {
      state.deactivateTab(1);
      assert.equal(state.isTabInactive(1), true);
    });
  });

  describe('.isTabErrored', function () {
    it('returns true if the tab is errored', function () {
      state.errorTab(1);
      assert.equal(state.isTabErrored(1), true);
    });
  });

  describe('.updateAnnotationCount()', function() {
    var server;

    beforeEach(function() {
      server = sinon.fakeServer.create({
        autoRespond: true,
        respondImmediately: true
      });
      server.respondWith(
        "GET", "http://example.com/badge?uri=tabUrl",
        [200, {}, '{"total": 1}']
      );
      sinon.stub(console, 'error');
    });

    afterEach(function() {
      server.restore();
      console.error.restore();
    });

    it('sends the correct XMLHttpRequest to the server', function() {
      state.updateAnnotationCount("tabId", "tabUrl", "http://example.com");

      assert.equal(server.requests.length, 1);
      var request = server.requests[0];
      assert.equal(request.method, "GET");
      assert.equal(request.url, "http://example.com/badge?uri=tabUrl");
    });

    it('urlencodes the tabUrl appropriately', function() {
      state.updateAnnotationCount("tabId", "http://foo.com?bar=baz qüx", "http://example.com");

      assert.equal(server.requests.length, 1);
      var request = server.requests[0];
      assert.equal(request.method, "GET");
      assert.equal(request.url, "http://example.com/badge?uri=http%3A%2F%2Ffoo.com%3Fbar%3Dbaz+q%C3%BCx");
    });

    it("doesn't set the annotation count if the server's JSON is invalid", function() {
      server.respondWith(
        "GET", "http://example.com/badge?uri=tabUrl",
        [200, {}, 'this is not valid json']
      );

      state.updateAnnotationCount("tabId", "tabUrl", "http://example.com");
      assert.equal(state.annotationCount("tabId"), 0);
    });

    it("logs an error if the server's JSON is invalid", function() {
      server.respondWith(
        "GET", "http://example.com/badge?uri=tabUrl",
        [200, {}, 'this is not valid json']
      );

      state.updateAnnotationCount("tabId", "tabUrl", "http://example.com");
      assert(console.error.called);
    });

    it("doesn't set the annotation count if the server's total is invalid", function() {
      server.respondWith(
        "GET", "http://example.com/badge?uri=tabUrl",
        [200, {}, '{"total": "not a valid number"}']
      );

      state.updateAnnotationCount("tabId", "tabUrl", "http://example.com");
      assert.equal(state.annotationCount("tabId"), 0);
    });

    it("logs an error if the server's total is invalid", function() {
      server.respondWith(
        "GET", "http://example.com/badge?uri=tabUrl",
        [200, {}, '{"total": "not a valid number"}']
      );

      state.updateAnnotationCount("tabId", "tabUrl", "http://example.com");
      assert(console.error.called);
    });

    it("doesn't set the annotation count if the server response has no total", function() {
      server.respondWith(
        "GET", "http://example.com/badge?uri=tabUrl",
        [200, {}, '{"rows": []}']
      );

      state.updateAnnotationCount("tabId", "tabUrl", "http://example.com");
      assert.equal(state.annotationCount("tabId"), 0);
    });

    it("logs an error if the server response has no total", function() {
      server.respondWith(
        "GET", "http://example.com/badge?uri=tabUrl",
        [200, {}, '{"rows": []}']
      );

      state.updateAnnotationCount("tabId", "tabUrl", "http://example.com");
      assert(console.error.called);
    });
  });
});
