'use strict';

var proxyquire = require('proxyquire');

var util = require('./util');

/**
 * Disable calling through to the original module for a stub.
 *
 * By default proxyquire will call through to the original module
 * for any methods not provided by a stub. This function disables
 * this behavior for a stub and returns the input stub.
 *
 * This prevents unintended usage of the original dependency.
 */
function noCallThru(stub) {
  return Object.assign(stub, {'@noCallThru':true});
}

describe('markdown', function () {
  function isHidden(element) {
    return element.classList.contains('ng-hide');
  }

  function inputElement(editor) {
    return editor[0].querySelector('.form-input');
  }

  function viewElement(editor) {
    return editor[0].querySelector('.styled-text');
  }

  function getRenderedHTML(editor) {
    var contentElement = viewElement(editor);
    if (isHidden(contentElement)) {
      return 'rendered markdown is hidden';
    }
    return contentElement.innerHTML;
  }

  before(function () {
    angular.module('app', ['ngSanitize'])
      .directive('markdown', proxyquire('../markdown', {
        angular: noCallThru(require('angular')),
        katex: {
          renderToString: function (input) {
            return 'math:' + input.replace(/$$/g, '');
          },
        },
        '@noCallThru': true,
      }))
      .filter('converter', function () {
        return function (input) {
          return 'rendered:' + input;
        };
      });
  });

  beforeEach(function () {
    angular.mock.module('app');
    angular.mock.module('h.templates');
  });

  describe('read only state', function () {
    it('should show the rendered view when readOnly is true', function () {
      var editor = util.createDirective(document, 'markdown', {
        readOnly: true,
        ngModel: 'Hello World',
      });
      assert.isTrue(isHidden(inputElement(editor)));
      assert.isFalse(isHidden(viewElement(editor)));
    });

    it('should show the editor when readOnly is false', function () {
      var editor = util.createDirective(document, 'markdown', {
        readOnly: false,
        ngModel: 'Hello World',
      });
      assert.isFalse(isHidden(inputElement(editor)));
      assert.isTrue(isHidden(viewElement(editor)));
    });
  });

  describe('rendering', function () {
    it('should render input markdown', function () {
      var editor = util.createDirective(document, 'markdown', {
        readOnly: true,
        ngModel: 'Hello World',
      });
      assert.equal(getRenderedHTML(editor), 'rendered:Hello World');
    });
  });

  describe('math rendering', function () {
    it('should render LaTeX', function () {
      var editor = util.createDirective(document, 'markdown', {
        readOnly: true,
        ngModel: '$$x*2$$',
      });
      assert.equal(getRenderedHTML(editor),
        'rendered:math:\\displaystyle {x*2}rendered:');
    });
  });
});
