var proxyquire = require('proxyquire');

describe('raven', function () {
  var fakeRavenJS;
  var raven;

  beforeEach(function () {
    fakeRavenJS = {
      config: sinon.stub().returns({
        install: sinon.stub(),
      }),
      captureException: sinon.stub(),
    };
    raven = proxyquire('../raven', {
      'raven-js': fakeRavenJS,
    });
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
});
