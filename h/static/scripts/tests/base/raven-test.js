'use strict';

const proxyquire = require('proxyquire');
const noCallThru = require('../util').noCallThru;

describe('raven', () => {
  let fakeRavenJS;
  let raven;

  beforeEach(() => {
    fakeRavenJS = {
      config: sinon.stub().returns({
        install: sinon.stub(),
      }),

      captureException: sinon.stub(),
    };

    raven = proxyquire('../../base/raven', noCallThru({
      'raven-js': fakeRavenJS,
    }));
  });

  describe('.install()', () => {
    it('installs a handler for uncaught promises', () => {
      raven.init({
        dsn: 'dsn',
        release: 'release',
      });
      const event = document.createEvent('Event');
      event.initEvent('unhandledrejection', true /* bubbles */, true /* cancelable */);
      event.reason = new Error('Some error');
      window.dispatchEvent(event);

      assert.calledWith(fakeRavenJS.captureException, event.reason,
        sinon.match.any);
    });
  });

  describe('.report()', () => {
    it('extracts the message property from Error-like objects', () => {
      raven.report({message: 'An error'}, 'context');
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
