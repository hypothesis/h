describe('BrowserAction', function () {
  'use strict';

  var BrowserAction = h.BrowserAction;
  var TabState = h.TabState;
  var action;
  var fakeChromeBrowserAction;

  beforeEach(function () {
    fakeChromeBrowserAction = {
      setIcon: sinon.spy(),
      setTitle: sinon.spy(),
      getBadgeText: function(args, func) {
        func('');
      },
      setBadgeText: sinon.spy()
    };
    action = new BrowserAction(fakeChromeBrowserAction);
  });

  describe('.activate', function () {
    it('sets the active browser icon', function () {
      var spy = fakeChromeBrowserAction.setIcon;
      action.activate(1);
      assert.calledWith(spy, {
        tabId: 1,
        path: BrowserAction.icons[TabState.states.ACTIVE],
      });
    });

    it('sets the title of the browser icon', function () {
      var spy = fakeChromeBrowserAction.setTitle;
      action.activate(1);
      assert.calledWith(spy, {
        tabId: 1,
        title: 'Hypothesis is active'
      });
    });

    it('does not set the title if there is badge text showing', function () {
      var originalGetBadgeTextFunc = fakeChromeBrowserAction.getBadgeText;
      fakeChromeBrowserAction.getBadgeText = function(args, func) {
        func('9');  // The number of annotations is showing on the badge.
      };

      action.activate(1);

      assert.notCalled(fakeChromeBrowserAction.setTitle);
      fakeChromeBrowserAction.getBadgeText = originalGetBadgeTextFunc;
    });
  });

  describe('.deactivate', function () {
    it('sets the inactive browser icon', function () {
      var spy = fakeChromeBrowserAction.setIcon;
      action.deactivate(1);
      assert.calledWith(spy, {
        tabId: 1,
        path: BrowserAction.icons[TabState.states.INACTIVE],
      });
    });

    it('sets the title of the browser icon', function () {
      var spy = fakeChromeBrowserAction.setTitle;
      action.deactivate(1);
      assert.calledWith(spy, {
        tabId: 1,
        title: 'Hypothesis is inactive'
      });
    });

    it('does not set the title if there is badge text showing', function () {
      var originalGetBadgeTextFunc = fakeChromeBrowserAction.getBadgeText;
      fakeChromeBrowserAction.getBadgeText = function(args, func) {
        func('9');  // The number of annotations is showing on the badge.
      };

      action.deactivate(1);

      assert.notCalled(fakeChromeBrowserAction.setTitle);
      fakeChromeBrowserAction.getBadgeText = originalGetBadgeTextFunc;
    });
  });

  describe('.error', function () {
    it('sets the inactive browser icon', function () {
      var spy = fakeChromeBrowserAction.setIcon;
      action.error(1);
      assert.calledWith(spy, {
        tabId: 1,
        path: BrowserAction.icons[TabState.states.INACTIVE],
      });
    });

    it('sets the title of the browser icon', function () {
      var spy = fakeChromeBrowserAction.setTitle;
      action.error(1);
      assert.calledWith(spy, {
        tabId: 1,
        title: 'Hypothesis has failed to load'
      });
    });

    it('still sets the title even there is badge text showing', function () {
      var originalGetBadgeTextFunc = fakeChromeBrowserAction.getBadgeText;
      fakeChromeBrowserAction.getBadgeText = function(args, func) {
        func('9');  // The number of annotations is showing on the badge.
      };

      action.error(1);

      assert.calledWith(fakeChromeBrowserAction.setTitle, {
        tabId: 1,
        title: 'Hypothesis has failed to load'
      });
      fakeChromeBrowserAction.getBadgeText = originalGetBadgeTextFunc;
    });

    it('shows a badge', function () {
      var spy = fakeChromeBrowserAction.setBadgeText;
      action.error(1);
      assert.calledWith(spy, {
        tabId: 1,
        text: '!'
      });
    });
  });

  describe('.setState', function () {
    it('allows the state to be set via a constant', function () {
      var spy = fakeChromeBrowserAction.setIcon;
      action.setState(1, TabState.states.ACTIVE);
      assert.calledWith(spy, {
        tabId: 1,
        path: BrowserAction.icons[TabState.states.ACTIVE],
      });
    });
  });

  describe('.updateBadge()', function() {
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
      action.updateBadge("tabId", "tabUrl", "http://example.com");

      assert(server.requests.length === 1);
      var request = server.requests[0];
      assert(request.method === "GET");
      assert(request.url === "http://example.com/badge?uri=tabUrl");
    });

    it("doesn't set the badge if the server's JSON is invalid", function() {
      server.respondWith(
        "GET", "http://example.com/badge?uri=tabUrl",
        [200, {}, 'this is not valid json']
      );

      action.updateBadge("tabId", "tabUrl", "http://example.com");

      assert(fakeChromeBrowserAction.setBadgeText.notCalled);
      assert(fakeChromeBrowserAction.setTitle.notCalled);
    });

    it("logs an error if the server's JSON is invalid", function() {
      server.respondWith(
        "GET", "http://example.com/badge?uri=tabUrl",
        [200, {}, 'this is not valid json']
      );

      action.updateBadge("tabId", "tabUrl", "http://example.com");

      assert(console.error.called);
    });

    it("doesn't set the badge if the server's total is invalid", function() {
      server.respondWith(
        "GET", "http://example.com/badge?uri=tabUrl",
        [200, {}, '{"total": "not a valid number"}']
      );

      action.updateBadge("tabId", "tabUrl", "http://example.com");

      assert(fakeChromeBrowserAction.setBadgeText.notCalled);
      assert(fakeChromeBrowserAction.setTitle.notCalled);
    });

    it("logs an error if the server's total is invalid", function() {
      server.respondWith(
        "GET", "http://example.com/badge?uri=tabUrl",
        [200, {}, '{"total": "not a valid number"}']
      );

      action.updateBadge("tabId", "tabUrl", "http://example.com");

      assert(console.error.called);
    });

    it("doesn't set the badge if server response has no total", function() {
      server.respondWith(
        "GET", "http://example.com/badge?uri=tabUrl",
        [200, {}, '{"rows": []}']
      );

      action.updateBadge("tabId", "tabUrl", "http://example.com");

      assert(fakeChromeBrowserAction.setBadgeText.notCalled);
      assert(fakeChromeBrowserAction.setTitle.notCalled);
    });

    it("logs an error if the server response has no total", function() {
      server.respondWith(
        "GET", "http://example.com/badge?uri=tabUrl",
        [200, {}, '{"rows": []}']
      );

      action.updateBadge("tabId", "tabUrl", "http://example.com");

      assert(console.error.called);
    });

    it("sets the browserAction's badge text", function() {
      server.respondWith(
        "GET", "http://example.com/badge?uri=tabUrl",
        [200, {}, '{"total": 23}']
      );

      action.updateBadge("tabId", "tabUrl", "http://example.com");

      assert(fakeChromeBrowserAction.setBadgeText.calledOnce);
      assert(fakeChromeBrowserAction.setBadgeText.calledWithExactly(
        {tabId: "tabId", text: "23"}));
    });

    it("sets the browserAction's title badge text when there's 1 annotation",
        function() {
      server.respondWith(
        "GET", "http://example.com/badge?uri=tabUrl",
        [200, {}, '{"total": 1}']
      );

      action.updateBadge("tabId", "tabUrl", "http://example.com");

      assert(fakeChromeBrowserAction.setTitle.calledOnce);
      assert(fakeChromeBrowserAction.setTitle.calledWithExactly(
        {tabId: "tabId", title: "There's 1 annotation on this page"}));
    });

    it("sets the browserAction's title badge text when there's >1 annotation",
        function() {
      server.respondWith(
        "GET", "http://example.com/badge?uri=tabUrl",
        [200, {}, '{"total": 23}']
      );

      action.updateBadge("tabId", "tabUrl", "http://example.com");

      assert(fakeChromeBrowserAction.setTitle.calledOnce);
      assert(fakeChromeBrowserAction.setTitle.calledWithExactly(
        {tabId: "tabId", title: "There are 23 annotations on this page"}));
    });

    it("does not set the badge text if there are 0 annotations", function() {
      server.respondWith(
        "GET", "http://example.com/badge?uri=tabUrl",
        [200, {}, '{"total": 0}']
      );

      action.updateBadge("tabId", "tabUrl", "http://example.com");

      assert(fakeChromeBrowserAction.setBadgeText.notCalled);
    });

    it("does not set the badge title if there are 0 annotations", function() {
      server.respondWith(
        "GET", "http://example.com/badge?uri=tabUrl",
        [200, {}, '{"total": 0}']
      );

      action.updateBadge("tabId", "tabUrl", "http://example.com");

      assert(fakeChromeBrowserAction.setTitle.notCalled);
    });

    it("truncates numbers greater than 999 to '999+'", function() {
      server.respondWith(
        "GET", "http://example.com/badge?uri=tabUrl",
        [200, {}, '{"total": 1001}']
      );

      action.updateBadge("tabId", "tabUrl", "http://example.com");

      assert(fakeChromeBrowserAction.setBadgeText.calledOnce);
      assert(fakeChromeBrowserAction.setBadgeText.calledWithExactly(
        {tabId: "tabId", text: "999+"}));
      assert(fakeChromeBrowserAction.setTitle.calledWithExactly(
        {tabId: "tabId", title: "There are 999+ annotations on this page"}));
    });

    it("does not set the badge text if there is existing text", function() {
      server.respondWith(
        "GET", "http://example.com/badge?uri=tabUrl",
        [200, {}, '{"total": 23}']
      );
      var originalGetBadgeTextFunc = fakeChromeBrowserAction.getBadgeText;

      fakeChromeBrowserAction.getBadgeText = function(args, func) {
        func('some badge text that is already showing');
      };
      action.updateBadge("tabId", "tabUrl", "http://example.com");
      fakeChromeBrowserAction.getBadgeText = originalGetBadgeTextFunc;

      assert(fakeChromeBrowserAction.setBadgeText.notCalled);
    });

    it("does not set the badge title if there is existing text", function() {
      server.respondWith(
        "GET", "http://example.com/badge?uri=tabUrl",
        [200, {}, '{"total": 23}']
      );
      var originalGetBadgeTextFunc = fakeChromeBrowserAction.getBadgeText;

      fakeChromeBrowserAction.getBadgeText = function(args, func) {
        func('some badge text that is already showing');
      };
      action.updateBadge("tabId", "tabUrl", "http://example.com");
      fakeChromeBrowserAction.getBadgeText = originalGetBadgeTextFunc;

      assert(fakeChromeBrowserAction.setTitle.notCalled);
    });
  });
});
