'use strict';

var proxyquire = require('proxyquire');

describe('errors', function () {
  var fakeRaven;
  var errors;

  beforeEach(function () {
    fakeRaven = {
      report: sinon.stub(),
    };
    errors = proxyquire('../lib/errors', {
      '../../../static/scripts/raven': fakeRaven,
    });
    sinon.stub(console, 'error');
  });

  afterEach(function () {
    console.error.restore();
  });

  describe('.report', function () {
    it('reports unknown errors via Raven', function () {
      var error = new Error('A most unexpected error');
      errors.report('injecting the sidebar failed', error);
      assert.calledWith(fakeRaven.report,
                        'injecting the sidebar failed', error);
    });

    it('does not report known errors via Raven', function () {
      var error = new errors.LocalFileError('some message');
      errors.report('injecting the sidebar failed', error);
      assert.notCalled(fakeRaven.report);
    });
  });
});
