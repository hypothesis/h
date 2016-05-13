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

  describe('#shouldIgnoreInjectionError', function () {
    var ignoredErrors = [
      'The tab was closed',
      'No tab with id 42',
      'Cannot access contents of url "file:///C:/t/cpp.pdf". ' +
      'Extension manifest must request permission to access this host.',
      'Cannot access contents of page',
      'The extensions gallery cannot be scripted.',
    ];

    var unexpectedErrors = [
      'SyntaxError: A typo',
    ];

    it('should be true for "expected" errors', function () {
      ignoredErrors.forEach(function (message) {
        var error = {message: message};
        assert.isTrue(errors.shouldIgnoreInjectionError(error));
      });
    });

    it('should be false for unexpected errors', function () {
      unexpectedErrors.forEach(function (message) {
        var error = {message: message};
        assert.isFalse(errors.shouldIgnoreInjectionError(error));
      });
    });

    it('should be true for the extension\'s custom error classes', function () {
      var error = new errors.LocalFileError('some message');
      assert.isTrue(errors.shouldIgnoreInjectionError(error));
    });
  });

  describe('#report', function () {
    it('reports unknown errors via Raven', function () {
      var error = new Error('A most unexpected error');
      errors.report(error, 'injecting the sidebar');
      assert.calledWith(fakeRaven.report, error, 'injecting the sidebar');
    });

    it('does not report known errors via Raven', function () {
      var error = new errors.LocalFileError('some message');
      errors.report(error, 'injecting the sidebar');
      assert.notCalled(fakeRaven.report);
    });
  });
});
