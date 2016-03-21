'use strict';

var angular = require('angular');
var proxyquire = require('proxyquire');

var util = require('./util');
var noCallThru = require('../../test/util').noCallThru;

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

  function mockFormattingCommand() {
    return {
      text: 'formatted text',
      selectionStart: 0,
      selectionEnd: 0,
    };
  }

  before(function () {
    angular.module('app', ['ngSanitize'])
      .directive('markdown', proxyquire('../markdown', noCallThru({
        angular: angular,
        katex: {
          renderToString: function (input) {
            return 'math:' + input.replace(/$$/g, '');
          },
        },
        '../markdown-commands': {
          convertSelectionToLink: mockFormattingCommand,
          toggleBlockStyle: mockFormattingCommand,
          toggleSpanStyle: mockFormattingCommand,
          LinkType: require('../../markdown-commands').LinkType,
        },
      })))
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

  describe('toolbar buttons', function () {
    it('should apply formatting when clicking toolbar buttons', function () {
      var editor = util.createDirective(document, 'markdown', {
        readOnly: false,
        ngModel: 'Hello World',
      });
      var input = inputElement(editor);
      var buttons = editor[0].querySelectorAll('.markdown-tools-button');
      for (var i=0; i < buttons.length; i++) {
        input.value = 'original text';
        angular.element(buttons[i]).click();
        assert.equal(input.value, mockFormattingCommand().text);
      }
    });
  });

  describe('editing', function () {
    it('should update the input model', function () {
      var editor = util.createDirective(document, 'markdown', {
        readOnly: false,
        ngModel: 'Hello World',
      });
      var input = inputElement(editor);
      input.value = 'new text';
      util.sendEvent(input, 'change');
      assert.equal(editor.scope.ngModel, 'new text');
    });
  });
});
