var proxyquire = require('proxyquire');

describe('raven', function () {
  var fakeRavenJS = {
    config: sinon.stub().returns({
      install: sinon.stub(),
    }),
    captureException: sinon.stub(),
  };

  var raven;

  beforeEach(function () {
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
});
