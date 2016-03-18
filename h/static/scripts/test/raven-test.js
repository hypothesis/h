'use strict';

var proxyquire = require('proxyquire');
var noCallThru = require('./util').noCallThru;

function fakeExceptionData(scriptURL) {
  return {
    exception: {
      values: [{
        stacktrace: {
          frames: [{
            filename: scriptURL,
          }]
        }
      }]
    },
    culprit: scriptURL,
  };
}

describe('raven', function () {
  // A stub for the callback that the Angular plugin installs with
  // Raven.setDataCallback()
  var fakeAngularTransformer;
  var fakeAngularPlugin;
  var fakeRavenJS;
  var raven;

  beforeEach(function () {
    fakeRavenJS = {
      config: sinon.stub().returns({
        install: sinon.stub(),
      }),

      captureException: sinon.stub(),

      setDataCallback: function (callback) {
        this._globalOptions.dataCallback = callback;
      },

      _globalOptions: {
        dataCallback: undefined,
      },
    };

    fakeAngularTransformer = sinon.stub();
    fakeAngularPlugin = sinon.spy(function (Raven) {
      Raven.setDataCallback(fakeAngularTransformer);
    });

    raven = proxyquire('../raven', noCallThru({
      'raven-js': fakeRavenJS,
      'raven-js/plugins/angular': fakeAngularPlugin,
    }));
  });

  describe('.install()', function () {
    it('installs a handler for uncaught promises', function () {
      raven.init({
        dsn: 'dsn',
        release: 'release',
      });
      var event = document.createEvent('Event');
      event.initEvent('unhandledrejection', true /* bubbles */, true /* cancelable */);
      event.reason = new Error('Some error');
      window.dispatchEvent(event);

      assert.calledWith(fakeRavenJS.captureException, event.reason,
        sinon.match.any);
    });
  });

  describe('pre-submission data transformation', function () {
    var dataCallback;

    beforeEach(function () {
      raven.init({dsn: 'dsn', release: 'release'});
      var configOpts = fakeRavenJS.config.args[0][1];
      dataCallback = configOpts && configOpts.dataCallback;
    });

    it('installs a transformer', function () {
      assert.ok(dataCallback);
    });

    it('replaces non-HTTP URLs with filenames', function () {
      var scriptURL = 'chrome-extension://1234/public/bundle.js';
      var transformed = dataCallback(fakeExceptionData(scriptURL));
      assert.equal(transformed.culprit, 'bundle.js');
      var transformedStack = transformed.exception.values[0].stacktrace;
      assert.equal(transformedStack.frames[0].filename, 'bundle.js');
    });

    it('does not modify HTTP URLs', function () {
      var scriptURL = 'https://hypothes.is/assets/scripts/bundle.js';
      var transformed = dataCallback(fakeExceptionData(scriptURL));
      assert.equal(transformed.culprit, scriptURL);
      var transformedStack = transformed.exception.values[0].stacktrace;
      assert.equal(transformedStack.frames[0].filename, scriptURL);
    });
  });

  describe('.report()', function () {
    it('extracts the message property from Error-like objects', function () {
      raven.report({message: 'An error'}, 'context');
      assert.calledWith(fakeRavenJS.captureException, 'An error', {
        extra: {
          when: 'context',
        },
      });
    });

    it('passes extra details through', function () {
      var error = new Error('an error');
      raven.report(error, 'some operation', { url: 'foobar.com' });
      assert.calledWith(fakeRavenJS.captureException, error, {
        extra: {
          when: 'some operation',
          url: 'foobar.com',
        },
      });
    });
  });

  describe('.angularModule()', function () {
    var angularStub;

    beforeEach(function () {
      angularStub = {
        module: sinon.stub(),
      };
    });

    it('installs the Angular plugin', function () {
      raven.init('dsn');
      raven.angularModule(angularStub);
      assert.calledWith(fakeAngularPlugin, fakeRavenJS, angularStub);
    });

    it('installs the data transformers', function () {
      raven.init('dsn');
      var originalTransformer = sinon.stub();
      fakeRavenJS._globalOptions.dataCallback = originalTransformer;
      raven.angularModule(angularStub);
      fakeRavenJS._globalOptions.dataCallback(
        fakeExceptionData('app.bundle.js')
      );

      // Check that both our data transformer and the one provided by
      // the Angular plugin were invoked
      assert.called(originalTransformer);
      assert.called(fakeAngularTransformer);
    });
  });
});
