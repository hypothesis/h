var module = angular.mock.module;
var inject = angular.mock.inject;

describe('spinner', function () {
  var $animate = null;
  var $element = null
  var sandbox = null;

  before(function () {
    angular.module('h', []).directive('spinner', require('../spinner'));
  });

  beforeEach(module('h'));

  beforeEach(inject(function (_$animate_, $compile, $rootScope) {
    sandbox = sinon.sandbox.create();

    $animate = _$animate_;
    sandbox.spy($animate, 'enabled');

    $element = angular.element('<span class="spinner"></span>');
    $compile($element)($rootScope.$new());
  }));

  afterEach(function () {
    sandbox.restore();
  });

  it('disables ngAnimate animations for itself', function () {
    assert.calledWith($animate.enabled, false, sinon.match($element));
  });
});
