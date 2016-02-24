'use strict';

/* globals MathJax */

var angular = require('angular');
var katex = require('katex');

var commands = require('../markdown-commands');
var mediaEmbedder = require('../media-embedder');

var loadMathJax = function() {
  if (!(typeof MathJax !== "undefined" && MathJax !== null)) {
    return $.ajax({
      url: "https://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS_HTML-full",
      dataType: 'script',
      cache: true,
      complete: function () {
        // MathJax configuration overides.
        return MathJax.Hub.Config({
          showMathMenu: false,
          displayAlign: "left"
        });
      }
    });
  }
};

/**
 * @ngdoc directive
 * @name markdown
 * @restrict A
 * @description
 * This directive controls both the rendering and display of markdown, as well as
 * the markdown editor.
 */
// @ngInject
module.exports = function($filter, $sanitize, $sce, $timeout) {
  return {
    link: function(scope, elem, attr, ctrl) {
      if (!(typeof ctrl !== "undefined" && ctrl !== null)) { return; }

      var input = elem[0].querySelector('.js-markdown-input');
      var inputEl = angular.element(input);
      var output = elem[0].querySelector('.js-markdown-preview');

      /**
       * Transform the editor's input field with an editor command.
       */
      function updateState(newStateFn) {
        var newState = newStateFn({
          text: input.value,
          selectionStart: input.selectionStart,
          selectionEnd: input.selectionEnd,
        });

        input.value = newState.text;
        input.selectionStart = newState.selectionStart;
        input.selectionEnd = newState.selectionEnd;

        // The input field currently loses focus when the contents are
        // changed. This re-focuses the input field but really it should
        // happen automatically.
        input.focus();
      }

      scope.insertBold = function() {
        updateState(function (state) {
          return commands.toggleSpanStyle(state, '**', '**', 'Bold');
        });
      };

      scope.insertItalic = function() {
        updateState(function (state) {
          return commands.toggleSpanStyle(state, '*', '*', 'Italic');
        });
      };

      scope.insertMath = function() {
        updateState(function (state) {
          var before = state.text.slice(0, state.selectionStart);

          if (before.length === 0 ||
              before.slice(-1) === '\n' ||
              before.slice(-2) === '$$') {
            return commands.toggleSpanStyle(state, '$$', '$$', 'Insert LaTeX');
          } else {
            return commands.toggleSpanStyle(state, '\\(', '\\)',
                                                'Insert LaTeX');
          }
        });
      };

      scope.insertLink = function() {
        updateState(function (state) {
          return commands.convertSelectionToLink(state);
        });
      };

      scope.insertIMG = function() {
        updateState(function (state) {
          return commands.convertSelectionToLink(state,
            commands.LinkType.IMAGE_LINK);
        });
      };

      scope.insertList = function() {
        updateState(function (state) {
          return commands.toggleBlockStyle(state, '* ');
        });
      };

      scope.insertNumList = function() {
        updateState(function (state) {
          return commands.toggleBlockStyle(state, '1. ');
        });
      };

      scope.insertQuote = function() {
        updateState(function (state) {
          return commands.toggleBlockStyle(state, '> ');
        });
      };

      // Keyboard shortcuts for bold, italic, and link.
      elem.on('keydown', function(e) {
        var shortcuts =
        {66: scope.insertBold,
          73: scope.insertItalic,
          75: scope.insertLink
        };

        var shortcut = shortcuts[e.keyCode];
        if (shortcut && (e.ctrlKey || e.metaKey)) {
          e.preventDefault();
          return shortcut();
        }
      });

      scope.preview = false;
      scope.togglePreview = function() {
        if (!scope.readOnly) {
          scope.preview = !scope.preview;
          if (scope.preview) {
            output.style.height = input.style.height;
            return ctrl.$render();
          } else {
            input.style.height = output.style.height;
            return $timeout(function() { return input.focus(); });
          }
        }
      };

      var mathJaxFallback = false;
      var renderInlineMath = function(textToCheck) {
        var re = /\\?\\\(|\\?\\\)/g;
        var startMath = null;
        var endMath = null;
        var match;
        var indexes = [];
        while ((match = re.exec(textToCheck))) {
          indexes.push(match.index);
        }
        for (var i = 0, index; i < indexes.length; i++) {
          index = indexes[i];
          if (startMath === null) {
            startMath = index + 2;
          } else {
            endMath = index;
          }
          if (startMath !== null && endMath !== null) {
            try {
              var math = katex.renderToString(textToCheck.substring(startMath, endMath));
              textToCheck = (
                  textToCheck.substring(0, (startMath - 2)) + math +
                  textToCheck.substring(endMath + 2)
                  );
              startMath = null;
              endMath = null;
              return renderInlineMath(textToCheck);
            } catch (error) {
              loadMathJax();
              mathJaxFallback = true;
              $sanitize(textToCheck.substring(startMath, endMath));
            }
          }
        }
        return textToCheck;
      };

      var renderMathAndMarkdown = function(textToCheck) {
        var convert = $filter('converter');
        var re = /\$\$/g;

        var startMath = 0;
        var endMath = 0;

        var indexes = (function () {
          var match;
          var result = [];
          while ((match = re.exec(textToCheck))) {
            result.push(match.index);
          }
          return result;
        })();
        indexes.push(textToCheck.length);

        var parts = (function () {
          var result = [];

          /* jshint -W083 */
          for (var i = 0, index; i < indexes.length; i++) {
            index = indexes[i];

            result.push((function () {
              if (startMath > endMath) {
                endMath = index + 2;
                try {
                  // \\displaystyle tells KaTeX to render the math in display style (full sized fonts).
                  return katex.renderToString($sanitize("\\displaystyle {" + textToCheck.substring(startMath, index) + "}"));
                } catch (error) {
                  loadMathJax();
                  mathJaxFallback = true;
                  return $sanitize(textToCheck.substring(startMath, index));
                }
              } else {
                startMath = index + 2;
                return $sanitize(convert(renderInlineMath(textToCheck.substring(endMath, index))));
              }
            })());
          }
          /* jshint +W083 */
          return result;
        })();

        var htmlString = parts.join('');

        // Transform the HTML string into a DOM element.
        var domElement = document.createElement('div');
        domElement.innerHTML = htmlString;

        mediaEmbedder.replaceLinksWithEmbeds(domElement);

        return domElement.innerHTML;
      };

      // Re-render the markdown when the view needs updating.
      ctrl.$render = function() {
        if (!scope.readOnly && !scope.preview) {
          input.value = ctrl.$viewValue || '';
        }
        var value = ctrl.$viewValue || '';
        output.innerHTML = renderMathAndMarkdown(value);
        if (mathJaxFallback) {
          return $timeout((function() {
            return ((typeof MathJax !== "undefined" && MathJax !== null) ? MathJax.Hub : undefined).Queue(['Typeset', MathJax.Hub, output]);
          }), 0, false);
        }
      };

      // React to the changes to the input
      inputEl.bind('blur change keyup', function() {
        ctrl.$setViewValue(input.value);
      });

      // Reset height of output div in case it has been changed.
      // Re-render when it becomes uneditable.
      // Auto-focus the input box when the widget becomes editable.
      return scope.$watch('readOnly', function(readOnly) {
        scope.preview = false;
        output.style.height = "";
        ctrl.$render();
        if (!readOnly) {
          input.focus();
        }
      });
    },

    require: '?ngModel',
    restrict: 'E',
    scope: {
      readOnly: '<',
      required: '@'
    },
    templateUrl: 'markdown.html'
  };
};
