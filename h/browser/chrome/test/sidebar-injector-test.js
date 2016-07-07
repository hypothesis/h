'use strict';

var toResult = require('../../../static/scripts/test/promise-util').toResult;

// The root URL for the extension returned by the
// extensionURL(path) fake
var EXTENSION_BASE_URL = 'chrome-extension://hypothesis';

var PDF_VIEWER_BASE_URL = EXTENSION_BASE_URL + '/content/web/viewer.html?file=';

/**
 * Creates an <iframe> for testing the effects of code injected
 * into the page by the sidebar injector
 */
function createTestFrame() {
  var frame = document.createElement('iframe');
  document.body.appendChild(frame);
  frame.contentDocument.body.appendChild = function () {
    // no-op to avoid trying to actually load <script> tags injected into
    // the page
  };
  return frame;
}

describe('SidebarInjector', function () {
  var errors = require('../lib/errors');
  var SidebarInjector = require('../lib/sidebar-injector');
  var injector;
  var fakeChromeTabs;
  var fakeFileAccess;

  // The content type that the detection script injected into
  // the page should report ('HTML' or 'PDF')
  var contentType;
  // The return value from the content script which checks whether
  // the sidebar has already been injected into the page
  var isAlreadyInjected;

  // An <iframe> created by some tests to verify the effects on the DOM of
  // code injected into the page by the sidebar
  var contentFrame;

  // Mock return value from embed.js when injected into page
  var embedScriptReturnValue;

  beforeEach(function () {
    contentType = 'HTML';
    isAlreadyInjected = false;
    contentFrame = undefined;
    embedScriptReturnValue = {
      installedURL: EXTENSION_BASE_URL + '/public/app.html',
    };

    var executeScriptSpy = sinon.spy(function (tabId, details, callback) {
      if (contentFrame) {
        contentFrame.contentWindow.eval(details.code);
      }

      if (details.code && details.code.match(/detectContentType/)) {
        callback([{type: contentType}]);
      } else if (details.file && details.file.match(/embed/)) {
        callback([embedScriptReturnValue]);
      } else if (details.file && details.file.match(/destroy/)) {
        callback([isAlreadyInjected]);
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
        return EXTENSION_BASE_URL + path;
      })
    });
  });

  afterEach(function () {
    if (contentFrame) {
      contentFrame.parentNode.removeChild(contentFrame);
    }
  });

  describe('.injectIntoTab', function () {
    var urls = [
      'chrome://version',
      'chrome-devtools://host',
      'chrome-extension://1234/foo.html',
      'chrome-extension://1234/foo.pdf',
    ];
    urls.forEach(function (url) {
      it('bails early when trying to load an unsupported url: ' + url, function () {
        var spy = fakeChromeTabs.executeScript;
        return toResult(injector.injectIntoTab({id: 1, url: url}))
          .then(function (result) {
          assert.ok(result.error);
          assert.instanceOf(result.error, errors.RestrictedProtocolError);
          assert.notCalled(spy);
        });
      });
    });

    it('succeeds if the tab is already displaying the embedded PDF viewer', function () {
        var url = PDF_VIEWER_BASE_URL +
          encodeURIComponent('http://origin/foo.pdf');
        return injector.injectIntoTab({id: 1, url: url});
      }
    );

    describe('when viewing a remote PDF', function () {
      var url = 'http://example.com/foo.pdf';

      it('injects hypothesis into the page', function () {
        contentType = 'PDF';
        var spy = fakeChromeTabs.update.yields({tab: 1});
        return injector.injectIntoTab({id: 1, url: url}).then(function() {
          assert.calledWith(spy, 1, {
            url: PDF_VIEWER_BASE_URL + encodeURIComponent(url)
          });
        });
      });

      it('preserves #annotations fragments in the URL', function () {
        contentType = 'PDF';
        var spy = fakeChromeTabs.update.yields({tab: 1});
        var hash = '#annotations:456';
        return injector.injectIntoTab({id: 1, url: url + hash})
          .then(function () {
          assert.calledWith(spy, 1, {
            url: PDF_VIEWER_BASE_URL + encodeURIComponent(url) + hash,
          });
        });
      });
    });

    describe('when viewing a remote HTML page', function () {
      it('injects hypothesis into the page', function () {
        var spy = fakeChromeTabs.executeScript;
        var url = 'http://example.com/foo.html';

        return injector.injectIntoTab({id: 1, url: url}).then(function() {
          assert.calledWith(spy, 1, {
            file: sinon.match('/public/embed.js')
          });
        });
      });

      it('reports an error if Hypothesis is already embedded', function () {
        embedScriptReturnValue = {installedURL: 'https://hypothes.is/app.html'};
        var url = 'http://example.com';
        return toResult(injector.injectIntoTab({id: 1, url: url}))
          .then(function (result) {
          assert.ok(result.error);
          assert.instanceOf(result.error, errors.AlreadyInjectedError);
        });
      });

      it('injects config options into the page', function () {
        contentFrame = createTestFrame();
        var url = 'http://example.com';
        return injector.injectIntoTab({id: 1, url: url}, {annotations:'456'})
          .then(function () {
            var configEl = contentFrame.contentDocument
              .querySelector('script.js-hypothesis-config');
            assert.ok(configEl);
            assert.deepEqual(JSON.parse(configEl.textContent),
              {annotations:'456'});
          });
      });
    });

    describe('when viewing a local PDF', function () {
      describe('when file access is enabled', function () {
        it('loads the PDFjs viewer', function () {
          var spy = fakeChromeTabs.update.yields([]);
          var url = 'file:///foo.pdf';
          contentType = 'PDF';

          return injector.injectIntoTab({id: 1, url: url}).then(
            function () {
              assert.called(spy);
              assert.calledWith(spy, 1, {
                url: PDF_VIEWER_BASE_URL + encodeURIComponent('file:///foo.pdf')
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
          return toResult(promise).then(function (result) {
            assert.instanceOf(result.error, errors.NoFileAccessError);
            assert.notCalled(fakeChromeTabs.executeScript);
          });
        });
      });

    describe('when viewing a local HTML file', function () {
      it('returns an error', function () {
        var url = 'file://foo.html';
        var promise = injector.injectIntoTab({id: 1, url: url});
        return toResult(promise).then(function (result) {
          assert.instanceOf(result.error, errors.LocalFileError);
        });
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
        var url = PDF_VIEWER_BASE_URL +
          encodeURIComponent('http://example.com/foo.pdf') + '#foo';
        return injector.removeFromTab({id: 1, url: url}).then(function () {
          assert.calledWith(spy, 1, {
            url: 'http://example.com/foo.pdf#foo'
          });
        });
      });

      it('drops #annotations fragments', function () {
        var spy = fakeChromeTabs.update.yields([]);
        var url = PDF_VIEWER_BASE_URL +
          encodeURIComponent('http://example.com/foo.pdf') + '#annotations:456';
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
            file: sinon.match('/public/destroy.js')
          });
        });
      });
    });
  });
});
