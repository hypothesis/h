import * as sentry from '../../base/sentry';

describe('sentry', () => {
  let fakeSentry;

  beforeEach(() => {
    fakeSentry = {
      init: sinon.stub(),
      captureException: sinon.stub(),
      setUser: sinon.stub(),
    };

    sentry.$imports.$mock({
      '@sentry/browser': fakeSentry,
    });
  });

  afterEach(() => {
    sentry.$imports.$restore();
  });

  describe('init', () => {
    it('configures the Sentry client', () => {
      sentry.init({
        dsn: 'dsn',
        environment: 'prod',
        release: 'release',
        userid: 'acct:foobar@hypothes.is',
      });
      assert.calledWith(
        fakeSentry.init,
        sinon.match({
          dsn: 'dsn',
          environment: 'prod',
          release: 'release',
        }),
      );
    });

    it('sets the user context when a userid is specified', () => {
      sentry.init({
        dsn: 'dsn',
        release: 'release',
        userid: 'acct:foobar@hypothes.is',
      });
      assert.calledWith(
        fakeSentry.setUser,
        sinon.match({
          id: 'acct:foobar@hypothes.is',
        }),
      );
    });

    it('does not set the user context when a userid is not specified', () => {
      sentry.init({
        dsn: 'dsn',
        release: 'release',
        userid: null,
      });
      assert.notCalled(fakeSentry.setUser);
    });
  });

  describe('report', () => {
    it('extracts the message property from Error-like objects', () => {
      sentry.report({ message: 'An error' }, 'context');
      assert.calledWith(fakeSentry.captureException, 'An error', {
        extra: {
          when: 'context',
        },
      });
    });

    it('passes extra details through', () => {
      const error = new Error('an error');
      sentry.report(error, 'some operation', { url: 'foobar.com' });
      assert.calledWith(fakeSentry.captureException, error, {
        extra: {
          when: 'some operation',
          url: 'foobar.com',
        },
      });
    });
  });
});
