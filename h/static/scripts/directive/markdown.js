'use strict';

var angular = require('angular');
var debounce = require('lodash.debounce');

var commands = require('../markdown-commands');
var mediaEmbedder = require('../media-embedder');
var renderMarkdown = require('../render-markdown');
var scopeTimeout = require('../util/scope-timeout');

/**
 * @ngdoc directive
 * @name markdown
 * @restrict A
 * @description
 * This directive controls both the rendering and display of markdown, as well as
 * the markdown editor.
 */
// @ngInject
module.exports = function($sanitize) {
  return {
    controller: function () {},
    link: function(scope, elem) {
      var input = elem[0].querySelector('.js-markdown-input');
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

      function focusInput() {
        // When the visibility of the editor changes, focus it.
        // A timeout is used so that focus() is not called until
        // the visibility change has been applied (by adding or removing
        // the relevant CSS classes)
        scopeTimeout(scope, function () {
          input.focus();
        }, 0);
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
      scope.togglePreview = function () {
        scope.preview = !scope.preview;
      };

      var handleInputChange = debounce(function () {
        scope.$apply(function () {
          scope.onEditText({text: input.value});
        });
      }, 100);
      input.addEventListener('input', handleInputChange);

      // Re-render the markdown when the view needs updating.
      scope.$watch('text', function () {
        output.innerHTML = renderMarkdown(scope.text || '', $sanitize);
        mediaEmbedder.replaceLinksWithEmbeds(output);
      });

      scope.showEditor = function () {
        return !scope.readOnly && !scope.preview;
      };

      // Exit preview mode when leaving edit mode
      scope.$watch('readOnly', function () {
        scope.preview = false;
      });

      scope.$watch('showEditor()', function (show) {
        if (show) {
          input.value = scope.text || '';
          focusInput();
        }
      });
    },

    restrict: 'E',
    scope: {
      readOnly: '<',
      text: '<?',
      onEditText: '&',
    },
    template: require('../../../templates/client/markdown.html'),
  };
};
