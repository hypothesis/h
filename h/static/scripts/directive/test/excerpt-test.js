'use strict';

var util = require('./util');
var excerpt = require('../excerpt');


describe('excerpt.Controller', function () {
  var ctrl;

  beforeEach(function() {
    ctrl = new excerpt.Controller();
    ctrl.overflowing = function () { return false; };
  });

  it('starts collapsed if the element is overflowing', function () {
    ctrl.overflowing = function () { return true; };

    assert.isTrue(ctrl.collapsed());
  });

  it('does not start collapsed if the element is not overflowing', function () {
    assert.isFalse(ctrl.collapsed());
  });

  it('is not initially uncollapsed if the element is overflowing', function () {
    assert.isFalse(ctrl.uncollapsed());
  });

  it('is not initially uncollapsed if the element is not overflowing', function () {
    assert.isFalse(ctrl.uncollapsed());
  });

  describe('.toggle()', function () {
    beforeEach(function () {
      ctrl.overflowing = function () { return true; };
    });

    it('toggles the collapsed state', function () {
      var a = ctrl.collapsed();
      ctrl.toggle();
      var b = ctrl.collapsed();
      ctrl.toggle();
      var c = ctrl.collapsed();

      assert.notEqual(a, b);
      assert.notEqual(b, c);
      assert.equal(a, c);
    });
  });
});


describe('excerpt.excerpt', function () {
  function excerptDirective(attrs, content) {
    return util.createDirective(document, 'excerpt', attrs, {}, content);
  }

  before(function () {
    angular.module('app', [])
      .directive('excerpt', excerpt.directive);
  });

  beforeEach(function () {
    angular.mock.module('app');
    angular.mock.module('h.templates');
  });

  it('renders its contents in a .excerpt element by default', function () {
    var element = excerptDirective({}, '<span id="foo"></span>');

    assert.equal(element.find('.excerpt #foo').length, 1);
  });

  it('when enabled, renders its contents in a .excerpt element', function () {
    var element = excerptDirective({enabled: true}, '<span id="foo"></span>');

    assert.equal(element.find('.excerpt #foo').length, 1);
  });

  it('when disabled, renders its contents but not in a .excerpt element', function () {
    var element = excerptDirective({enabled: false}, '<span id="foo"></span>');

    assert.equal(element.find('.excerpt #foo').length, 0);
    assert.equal(element.find('#foo').length, 1);
  });
});
