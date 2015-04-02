var angularMock = require('angular-mock');
var module = angularMock.module;
var inject = angularMock.inject;

var assert = chai.assert;
sinon.assert.expose(assert, {prefix: null});

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
