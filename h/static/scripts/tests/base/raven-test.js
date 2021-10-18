import * as raven from '../../base/raven';

describe('raven', () => {
  let fakeRavenJS;

  beforeEach(() => {
    fakeRavenJS = {
      config: sinon.stub().returns({
        install: sinon.stub(),
      }),

      captureException: sinon.stub(),
      setUserContext: sinon.stub(),
    };

    raven.$imports.$mock({
      'raven-js': { default: fakeRavenJS },
    });
  });

  afterEach(() => {
    raven.$imports.$restore();
  });

  describe('.init()', () => {
    it('configures the Sentry client', () => {
      raven.init({
        dsn: 'dsn',
        release: 'release',
        userid: 'acct:foobar@hypothes.is',
      });
      assert.calledWith(
        fakeRavenJS.config,
        'dsn',
        sinon.match({
          release: 'release',
        })
      );
    });

    it('sets the user context when a userid is specified', () => {
      raven.init({
        dsn: 'dsn',
        release: 'release',
        userid: 'acct:foobar@hypothes.is',
      });
      assert.calledWith(
        fakeRavenJS.setUserContext,
        sinon.match({
          id: 'acct:foobar@hypothes.is',
        })
      );
    });

    it('does not set the user context when a userid is not specified', () => {
      raven.init({
        dsn: 'dsn',
        release: 'release',
        userid: null,
      });
      assert.notCalled(fakeRavenJS.setUserContext);
    });

    it('installs a handler for uncaught promises', () => {
      raven.init({
        dsn: 'dsn',
        release: 'release',
      });
      const event = document.createEvent('Event');
      event.initEvent(
        'unhandledrejection',
        true /* bubbles */,
        true /* cancelable */
      );
      event.reason = new Error('Some error');
      window.dispatchEvent(event);

      assert.calledWith(
        fakeRavenJS.captureException,
        event.reason,
        sinon.match.any
      );
    });
  });

  describe('.report()', () => {
    it('extracts the message property from Error-like objects', () => {
      raven.report({ message: 'An error' }, 'context');
      assert.calledWith(fakeRavenJS.captureException, 'An error', {
        extra: {
          when: 'context',
        },
      });
    });

    it('passes extra details through', () => {
      const error = new Error('an error');
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
