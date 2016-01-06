describe('SidebarInjector', function () {
  'use strict';

  var errors = require('../lib/errors');
  var SidebarInjector = require('../lib/sidebar-injector');
  var injector;
  var fakeChromeTabs;
  var fakeFileAccess;

  // the content type that the detection script injected into
  // the page should report ('HTML' or 'PDF')
  var contentType;
  // the return value from the content script which checks whether
  // the sidebar has already been injected into the page
  var isAlreadyInjected;

  beforeEach(function () {
    contentType = 'HTML';
    isAlreadyInjected = false;

    var executeScriptSpy = sinon.spy(function (tabId, details, callback) {
      if (details.code.match(/window.annotator/)) {
        callback([isAlreadyInjected]);
      } else if (details.code.match(/detectContentType/)) {
        callback([{type: contentType}]);
      } else {
        callback([false]);
      }
    });

    fakeChromeTabs = {
      update: sinon.stub(),
      executeScript: executeScriptSpy,
    };
    fakeFileAccess = sinon.stub().yields(true);

    injector = new SidebarInjector(fakeChromeTabs, {
      isAllowedFileSchemeAccess: fakeFileAccess,
      extensionURL: sinon.spy(function (path) {
        return 'CRX_PATH' + path;
      })
    });
  });

  // Used when asserting rejected promises to raise an error if the resolved
  // path is taken. Otherwise Mocha will just assume the test passed.
  function assertReject() {
    assert(false, 'Expected the promise to reject the call');
  }

  describe('.injectIntoTab', function () {
    var protocols = ['chrome:', 'chrome-devtools:', 'chrome-extension:'];
    protocols.forEach(function (protocol) {
      it('bails early when trying to load an unsupported ' + protocol + ' url', function () {
        var spy = fakeChromeTabs.executeScript;
        var url = protocol + '//foo/';

        return injector.injectIntoTab({id: 1, url: url}).then(
          assertReject, function (err) {
            assert.instanceOf(err, errors.RestrictedProtocolError);
            assert.notCalled(spy);
          }
        );
      });
    });

    describe('when viewing a remote PDF', function () {
      it('injects hypothesis into the page', function () {
        contentType = 'PDF';
        var spy = fakeChromeTabs.update.yields({tab: 1});
        var url = 'http://example.com/foo.pdf';

        return injector.injectIntoTab({id: 1, url: url}).then(function() {
          assert.calledWith(spy, 1, {
            url: 'CRX_PATH/content/web/viewer.html?file=' + encodeURIComponent(url)
          });
        });
      });
    });

    describe('when viewing an remote HTML page', function () {
      it('injects hypothesis into the page', function () {
        var spy = fakeChromeTabs.executeScript;
        var url = 'http://example.com/foo.html';

        return injector.injectIntoTab({id: 1, url: url}).then(function() {
          assert.calledWith(spy, 1, {
            code: sinon.match('/public/config.js')
          });
          assert.calledWith(spy, 1, {
            code: sinon.match('/public/embed.js')
          });
        });
      });
    });

    describe('when viewing a local PDF', function () {
      describe('when file access is enabled', function () {
        it('loads the PDFjs viewer', function () {
          var spy = fakeChromeTabs.update.yields([]);
          var url = 'file://foo.pdf';
          contentType = 'PDF';

          return injector.injectIntoTab({id: 1, url: url}).then(
            function () {
              assert.called(spy);
              assert.calledWith(spy, 1, {
                url: 'CRX_PATH/content/web/viewer.html?file=' + encodeURIComponent('file://foo.pdf')
              });
            }
          );
        });
      });

      describe('when file access is disabled', function () {
        beforeEach(function () {
          fakeFileAccess.yields(false);
          contentType = 'PDF';
        });

        it('returns an error', function () {
          var url = 'file://foo.pdf';

          var promise = injector.injectIntoTab({id: 1, url: url});
          return promise.then(assertReject, function (err) {
            assert.instanceOf(err, errors.NoFileAccessError);
            assert.notCalled(fakeChromeTabs.executeScript);
          });
        });
      });

    describe('when viewing a local HTML file', function () {
      it('returns an error', function () {
        var url = 'file://foo.html';
        var promise = injector.injectIntoTab({id: 1, url: url});
        return promise.then(assertReject, function (err) {
          assert.instanceOf(err, errors.LocalFileError);
        });
      });

      it('retuns an error before loading the config', function () {
        var url = 'file://foo.html';
        var promise = injector.injectIntoTab({id: 1, url: url});
        return promise.then(assertReject, function (err) {
          assert.isFalse(fakeChromeTabs.executeScript.calledWith(1, {
            code: sinon.match(/config\.js/),
          }));
        });
      });
    });
  });

  describe("when there's a non-empty blocklist", function() {
    it("still injects the scripts on unblocked sites", function() {
      var promise = injector.injectIntoTab(
        {id: 1, url: "http://notblocked.com"});
      return promise.then(
        function onFulfill() {
          assert.called(fakeChromeTabs.executeScript);
        },
        function onRejected(reason) {
          assert(false, "The promise should not be rejected");
      });
    });

    it("still injects scripts on subdomains of blocked domains", function() {
      var promise = injector.injectIntoTab(
        {id: 1, url: "http://subdomain.twitter.com"});
      return promise.then(
        function onFulfill() {
          assert.called(fakeChromeTabs.executeScript);
        },
        function onRejected(reason) {
          assert(false, "The promise should not be rejected");
      });
    });

    it("doesn't inject any scripts on blocked sites", function() {
      var promise = injector.injectIntoTab({id: 1, url: "http://twitter.com"});
      return promise.then(
        function onFulfill() {
          assert(false, "The promise should not be fulfilled");
        },
        function onRejected(reason) {
          assert.notCalled(fakeChromeTabs.executeScript);
      });
    });

    it("doesn't inject scripts on sub pages of blocked sites", function() {
      var promise = injector.injectIntoTab(
        {id: 1, url: "http://twitter.com/sub/page.html"});
      return promise.then(
        function onFulfill() {
          assert(false, "The promise should not be fulfilled");
        },
        function onRejected(reason) {
          assert.notCalled(fakeChromeTabs.executeScript);
      });
    });

    it("doesn't inject scripts on blocked sites with queries", function() {
      var promise = injector.injectIntoTab(
        {id: 1, url: "http://twitter.com?tag=foo&user=bar"});
      return promise.then(
        function onFulfill() {
          assert(false, "The promise should not be fulfilled");
        },
        function onRejected(reason) {
          assert.notCalled(fakeChromeTabs.executeScript);
      });
    });

    it("doesn't inject scripts on blocked sites with anchors", function() {
      var promise = injector.injectIntoTab(
        {id: 1, url: "http://twitter.com#foo"});
      return promise.then(
        function onFulfill() {
          assert(false, "The promise should not be fulfilled");
        },
        function onRejected(reason) {
          assert.notCalled(fakeChromeTabs.executeScript);
      });
    });

    it("doesn't inject scripts on blocked sites with ports", function() {
      var promise = injector.injectIntoTab(
        {id: 1, url: "http://twitter.com:1234"});
      return promise.then(
        function onFulfill() {
          assert(false, "The promise should not be fulfilled");
        },
        function onRejected(reason) {
          assert.notCalled(fakeChromeTabs.executeScript);
      });
    });

    it("doesn't inject on wildcard-blocked subdomains", function() {
      var promise = injector.injectIntoTab(
        {id: 1, url: "http://drive.google.com"});
      return promise.then(
        function onFulfill() {
          assert(false, "The promise should not be fulfilled");
        },
        function onRejected(reason) {
          assert.notCalled(fakeChromeTabs.executeScript);
      });
    });
  });
});

  describe('.removeFromTab', function () {
    it('bails early when trying to unload a chrome url', function () {
      var spy = fakeChromeTabs.executeScript;
      var url = 'chrome://extensions/';

      return injector.removeFromTab({id: 1, url: url}).then(function () {
        assert.notCalled(spy);
      });
    });

    var protocols = ['chrome:', 'chrome-devtools:', 'chrome-extension:'];
    protocols.forEach(function (protocol) {
      it('bails early when trying to unload an unsupported ' + protocol + ' url', function () {
        var spy = fakeChromeTabs.executeScript;
        var url = protocol + '//foobar/';

        return injector.removeFromTab({id: 1, url: url}).then(function () {
          assert.notCalled(spy);
        });
      });
    });

    describe('when viewing a PDF', function () {
      it('reverts the tab back to the original document', function () {
        var spy = fakeChromeTabs.update.yields([]);
        var url = 'CRX_PATH/content/web/viewer.html?file=' + encodeURIComponent('http://example.com/foo.pdf');

        return injector.removeFromTab({id: 1, url: url}).then(function () {
          assert.calledWith(spy, 1, {
            url: 'http://example.com/foo.pdf'
          });
        });
      });
    });

    describe('when viewing an HTML page', function () {
      it('injects a destroy script into the page', function () {
        isAlreadyInjected = true;
        return injector.removeFromTab({id: 1, url: 'http://example.com/foo.html'}).then(function () {
          assert.calledWith(fakeChromeTabs.executeScript, 1, {
            code: sinon.match('/public/destroy.js')
          });
        });
      });
    });
  });

  describe('.detectContentType', function () {
    var el;
    beforeEach(function () {
      el = document.createElement('div');
      document.body.appendChild(el);
    });

    afterEach(function () {
      el.parentElement.removeChild(el);
    });

    it('matches the Chrome PDF viewer', function () {
      el.innerHTML =
       '<embed name="plugin" id="plugin" type="application/pdf"></embed>';
      assert.deepEqual(injector.detectContentType(el), { type: 'PDF' });
    });

    it('reports HTML by default', function () {
      el.innerHTML = '<div></div>';
      assert.deepEqual(injector.detectContentType(el), { type: 'HTML' } );
    });
  });
});
