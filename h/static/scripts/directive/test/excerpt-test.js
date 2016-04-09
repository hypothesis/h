'use strict';

var angular = require('angular');

var util = require('./util');
var excerpt = require('../excerpt');

describe('excerpt directive', function () {
  // ExcerptOverflowMonitor fake instance created by the current test
  var fakeOverflowMonitor;

  var SHORT_DIV = '<div id="foo" style="height:5px;"></div>';
  var TALL_DIV =  '<div id="foo" style="height:200px;">foo bar</div>';

  function excerptDirective(attrs, content) {
    var defaultAttrs = {
      enabled: true,
      contentData: 'the content',
      collapsedHeight: 40,
      inlineControls: false,
    };
    attrs = Object.assign(defaultAttrs, attrs);
    return util.createDirective(document, 'excerpt', attrs, {}, content);
  }

  before(function () {
    angular.module('app', [])
      .directive('excerpt', excerpt.directive);
  });

  beforeEach(function () {
    function FakeOverflowMonitor(ctrl) {
      fakeOverflowMonitor = this;

      this.ctrl = ctrl;
      this.check = sinon.stub();
      this.contentStyle = sinon.stub().returns({});
    }

    angular.mock.module('app');
    angular.mock.module(function ($provide) {
      $provide.value('ExcerptOverflowMonitor', FakeOverflowMonitor);
    });
  });

  context('when created', function () {
    it('schedules an overflow state recalculation', function () {
      excerptDirective({}, '<span id="foo"></span>');
      assert.called(fakeOverflowMonitor.check);
    });

    it('passes input properties to overflow state recalc', function () {
      var attrs = {
        animate: false,
        enabled: true,
        collapsedHeight: 40,
        inlineControls: false,
        overflowHysteresis: 20,
      };
      excerptDirective(attrs, '<span></span>');
      assert.deepEqual(fakeOverflowMonitor.ctrl.getState(), {
        animate: attrs.animate,
        enabled: attrs.enabled,
        collapsedHeight: attrs.collapsedHeight,
        collapse: true,
        overflowHysteresis: attrs.overflowHysteresis,
      });
    });

    it('reports the content height to ExcerptOverflowMonitor', function () {
      excerptDirective({}, TALL_DIV);
      assert.deepEqual(fakeOverflowMonitor.ctrl.contentHeight(), 200);
    });
  });

  context('input changes', function () {
    it('schedules an overflow state check when inputs change', function () {
      var element = excerptDirective({}, '<span></span>');
      fakeOverflowMonitor.check.reset();
      element.scope.contentData = 'new-content';
      element.scope.$digest();
      assert.calledOnce(fakeOverflowMonitor.check);
    });

    it('does not schedule a state check if inputs are unchanged', function () {
      var element = excerptDirective({}, '<span></span>');
      fakeOverflowMonitor.check.reset();
      element.scope.$digest();
      assert.notCalled(fakeOverflowMonitor.check);
    });
  });

  context('document events', function () {
    it('schedules an overflow check when media loads', function () {
      var element = excerptDirective({}, '<img src="https://example.com/foo.jpg">');
      fakeOverflowMonitor.check.reset();
      util.sendEvent(element[0], 'load');
      assert.called(fakeOverflowMonitor.check);
    });

    it('schedules an overflow check when the window is resized', function () {
      var element = excerptDirective({}, '<span></span>');
      fakeOverflowMonitor.check.reset();
      util.sendEvent(element[0].ownerDocument.defaultView, 'resize');
      assert.called(fakeOverflowMonitor.check);
    });
  });

  context('excerpt content style', function () {
    it('sets the content style using ExcerptOverflowMonitor#contentStyle()', function () {
      var element = excerptDirective({}, '<span></span>');
      fakeOverflowMonitor.contentStyle.returns({'max-height': '52px'});
      element.scope.$digest();
      var content = element[0].querySelector('.excerpt');
      assert.equal(content.style.cssText.trim(), 'max-height: 52px;');
    });
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
      fakeOverflowMonitor.ctrl.onOverflowChanged(true);
      var expandLink = findInlineControl(element[0]);
      assert.ok(expandLink);
      assert.equal(expandLink.querySelector('a').textContent, 'More');
    });

    it('does not display inline controls if not collapsed', function () {
      var element = excerptDirective({inlineControls: true}, SHORT_DIV);
      var expandLink = findInlineControl(element[0]);
      assert.notOk(expandLink);
    });

    it('toggles the expanded state when clicked', function () {
      var element = excerptDirective({inlineControls: true}, TALL_DIV);
      fakeOverflowMonitor.ctrl.onOverflowChanged(true);
      var expandLink = findInlineControl(element[0]);
      angular.element(expandLink.querySelector('a')).click();
      element.scope.$digest();
      var collapseLink = findInlineControl(element[0]);
      assert.equal(collapseLink.querySelector('a').textContent, 'Less');
    });
  });

  describe('bottom area', function () {
    it('expands the excerpt when clicking at the bottom if collapsed', function () {
      var element = excerptDirective({inlineControls: true},
        TALL_DIV);
      element.scope.$digest();
      assert.isTrue(element.ctrl.collapse);
      var bottomArea = element[0].querySelector('.excerpt__shadow');
      angular.element(bottomArea).click();
      assert.isFalse(element.ctrl.collapse);
    });
  });

  describe('#onCollapsibleChanged', function () {
    it('is called when overflow state changes', function () {
      var callback = sinon.stub();
      excerptDirective({
        onCollapsibleChanged: {
          args: ['collapsible'],
          callback: callback,
        }
      }, '<span></span>');
      fakeOverflowMonitor.ctrl.onOverflowChanged(true);
      assert.calledWith(callback, true);
      fakeOverflowMonitor.ctrl.onOverflowChanged(false);
      assert.calledWith(callback, false);
    });
  });
});
