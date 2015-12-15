'use strict';

var assign = require('core-js/modules/$.object-assign');
var util = require('./util');
var excerpt = require('../excerpt');

describe('excerpt directive', function () {
  var SHORT_DIV = '<div id="foo" style="height:5px;"></div>';
  var TALL_DIV =  '<div id="foo" style="height:200px;">foo bar</div>';

  function excerptDirective(attrs, content) {
    var defaultAttrs = {
      // disable animation so that expansion/collapse happens immediately
      // when the controls are toggled in tests
      animate: false,
      enabled: true,
      collapsedHeight: 40,
      inlineControls: false,
    };
    attrs = assign(defaultAttrs, attrs);
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

  describe('enabled state', function () {
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

  function isHidden(el) {
    return !el.offsetParent || el.classList.contains('ng-hide');
  }

  function findVisible(el, selector) {
    var elements = el.querySelectorAll(selector);
    for (var i=0; i < elements.length; i++) {
      if (!isHidden(elements[i])) {
        return elements[i];
      }
    }
    return undefined;
  }

  describe('inline controls', function () {
    function findInlineControl(el) {
      return findVisible(el, '.excerpt__toggle-link');
    }

    it('displays inline controls if collapsed', function () {
      var element = excerptDirective({inlineControls: true},
        TALL_DIV);
      element.scope.$digest();
      var expandLink = findInlineControl(element[0]);
      assert.ok(expandLink);
      assert.equal(expandLink.querySelector('a').textContent, 'More');
    });

    it('does not display inline controls if not collapsed', function () {
      var element = excerptDirective({inlineControls: true},
        SHORT_DIV);
      var expandLink = findInlineControl(element[0]);
      assert.notOk(expandLink);
    });

    it('toggles the expanded state when clicked', function () {
      var element = excerptDirective({inlineControls: true},
        TALL_DIV);
      element.scope.$digest();
      var expandLink = findInlineControl(element[0]);
      angular.element(expandLink.querySelector('a')).click();
      element.scope.$digest();
      var collapseLink = findInlineControl(element[0]);
      assert.equal(collapseLink.querySelector('a').textContent, 'Less');
    });
  });

  describe('.collapse', function () {
    function height(el) {
      return el.querySelector('.excerpt').offsetHeight;
    }

    it('collapses the body if collapse is true', function () {
      var element = excerptDirective({collapse: true}, TALL_DIV);
      assert.isBelow(height(element[0]), 100);
    });

    it('does not collapse the body if collapse is false', function () {
      var element = excerptDirective({collapse: false}, TALL_DIV);
      assert.isAbove(height(element[0]), 100);
    });
  });

  describe('.onCollapsibleChanged', function () {
    it('reports true if excerpt is tall', function () {
      var callback = sinon.stub();
      var element = excerptDirective({
        onCollapsibleChanged: {
          args: ['collapsible'],
          callback: callback,
        }
      }, TALL_DIV);
      assert.calledWith(callback, true);
    });

    it('reports false if excerpt is short', function () {
      var callback = sinon.stub();
      var element = excerptDirective({
        onCollapsibleChanged: {
          args: ['collapsible'],
          callback: callback,
        }
      }, SHORT_DIV);
      assert.calledWith(callback, false);
    });
  });
});
