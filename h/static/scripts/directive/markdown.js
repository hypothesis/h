'use strict';

var angular = require('angular');
var katex = require('katex');

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

      var userSelection = function() {
        if (input.selectionStart !== undefined) {
          var startPos = input.selectionStart;
          var endPos = input.selectionEnd;
          var selectedText = input.value.substring(startPos, endPos);
          var textBefore = input.value.substring(0, (startPos));
          var textAfter = input.value.substring(endPos);
          var selection = {
            before: textBefore,
            after: textAfter,
            selection: selectedText,
            start: startPos,
            end: endPos
          };
        }
        return selection;
      };

      var insertMarkup = function(value, selectionStart, selectionEnd) {
        // New value is set for the input
        input.value = value;
        // A new selection is set, or the cursor is positioned inside the input.
        input.selectionStart = selectionStart;
        input.selectionEnd = selectionEnd;
        // Focus the input
        return input.focus();
      };

      var applyInlineMarkup = function(markupL, innertext, markupR) {
        markupR || (markupR = markupL);
        var text = userSelection();
        if (text.selection === "") {
          var newtext = text.before + markupL + innertext + markupR + text.after;
          var start = (text.before + markupL).length;
          var end = (text.before + innertext + markupR).length;
          return insertMarkup(newtext, start, end);
        } else {
          // Check to see if markup has already been applied before to the selection.
          var slice1 = text.before.slice(text.before.length - markupL.length);
          var slice2 = text.after.slice(0, markupR.length);
          if (slice1 === markupL && slice2 === markupR) {
            // Remove markup
            newtext = (
                text.before.slice(0, (text.before.length - markupL.length)) +
                text.selection + text.after.slice(markupR.length)
                );
            start = text.before.length - markupL.length;
            end = (text.before + text.selection).length - markupR.length;
            return insertMarkup(newtext, start, end);
          } else {
            // Apply markup
            newtext = text.before + markupL + text.selection + markupR + text.after;
            start = (text.before + markupL).length;
            end = (text.before + text.selection + markupR).length;
            return insertMarkup(newtext, start, end);
          }
        }
      };

      scope.insertBold = function() {
        return applyInlineMarkup("**", "Bold");
      };

      scope.insertItalic = function() {
        return applyInlineMarkup("*", "Italic");
      };

      scope.insertMath = function() {
        var text = userSelection();
        var index = text.before.length;
        if (
            index === 0 ||
            input.value[index - 1] === '\n' ||
            (input.value[index - 1] === '$' && input.value[index - 2] === '$')
           ) {
          return applyInlineMarkup('$$', 'Insert LaTeX');
        } else {
          return applyInlineMarkup('\\(', 'Insert LaTeX', '\\)');
        }
      };

      scope.insertLink = function() {
        var text = userSelection();
        if (text.selection === "") {
          var newtext = text.before + "[Link Text](https://example.com)" + text.after;
          var start = text.before.length + 1;
          var end = text.before.length + 10;
          return insertMarkup(newtext, start, end);
        } else {
          // Check to see if markup has already been applied to avoid double presses.
          if (text.selection === "Link Text" || text.selection === "https://example.com") {
            return;
          }
          newtext = text.before + '[' + text.selection + '](https://example.com)' + text.after;
          start = (text.before + text.selection).length + 3;
          end = (text.before + text.selection).length + 22;
          return insertMarkup(newtext, start, end);
        }
      };

      scope.insertIMG = function() {
        var text = userSelection();
        if (text.selection === "") {
          var newtext = text.before + "![Image Description](https://yourimage.jpg)" + text.after;
          var start = text.before.length + 21;
          var end = text.before.length + 42;
          return insertMarkup(newtext, start, end);
        } else {
          // Check to see if markup has already been applied to avoid double presses.
          if (text.selection === "https://yourimage.jpg") {
            return;
          }
          newtext = text.before + '![' + text.selection + '](https://yourimage.jpg)' + text.after;
          start = (text.before + text.selection).length + 4;
          end = (text.before + text.selection).length + 25;
          return insertMarkup(newtext, start, end);
        }
      };

      scope.applyBlockMarkup = function(markup) {
        var text = userSelection();
        if (text.selection !== "") {
          var newstring = "";
          var index = text.before.length;
          if (index === 0) {
            // The selection takes place at the very start of the input
            for (var j = 0, char; j < text.selection.length; j++) {
              char = text.selection[j];
              if (char === "\n") {
                newstring = newstring + "\n" + markup;
              } else if (index === 0) {
                newstring = newstring + markup + char;
              } else {
                newstring = newstring + char;
              }
              index += 1;
            }
          } else {
            var newlinedetected = false;
            if (input.value.substring(index - 1).charAt(0) === "\n") {
              // Look to see if the selection falls at the beginning of a new line.
              newstring = newstring + markup;
              newlinedetected = true;
            }
            for (var k = 0, char; k < text.selection.length; k++) {
              char = text.selection[k];
              if (char === "\n") {
                newstring = newstring + "\n" + markup;
                newlinedetected = true;
              } else {
                newstring = newstring + char;
              }
              index += 1;
            }
            if (!newlinedetected) {
              // Edge case: The selection does not include any new lines and does not start at 0.
              // We need to find the newline before the currently selected text and add markup there.
              var i = 0;
              var indexoflastnewline = undefined;
              newstring = "";
              var iterable = text.before + text.selection;
              for (var i1 = 0, char; i1 < iterable.length; i1++) {
                char = iterable[i1];
                if (char === "\n") {
                  indexoflastnewline = i;
                }
                newstring = newstring + char;
                i++;
              }
              if (indexoflastnewline === undefined) {
                // The partial selection happens to fall on the firstline
                newstring = markup + newstring;
              } else {
                newstring = (
                    newstring.substring(0, (indexoflastnewline + 1)) +
                    markup + newstring.substring(indexoflastnewline + 1)
                    );
              }
              var value = newstring + text.after;
              var start = (text.before + markup).length;
              var end = (text.before + text.selection + markup).length;
              insertMarkup(value, start, end);
              return;
            }
          }
          // Sets input value and selection for cases where there are new lines in the selection
          // or the selection is at the start
          value = text.before + newstring + text.after;
          start = (text.before + newstring).length;
          end = (text.before + newstring).length;
          return insertMarkup(value, start, end);
        } else if (input.value.substring((text.start - 1 ), text.start) === "\n") {
          // Edge case, no selection, the cursor is on a new line.
          value = text.before + markup + text.selection + text.after;
          start = (text.before + markup).length;
          end = (text.before + markup).length;
          return insertMarkup(value, start, end);
        } else {
          // No selection, cursor is not on new line.
          // Check to see if markup has already been inserted.
          if (text.before.slice(text.before.length - markup.length) === markup) {
            var newtext = (
                text.before.substring(0, (index)) + "\n" +
                text.before.substring(index + 1 + markup.length) + text.after
                );
          }
          i = 0;
          for (var i2 = 0, char; i2 < text.before.length; i2++) {
            char = text.before[i2];
            if (char === "\n" && i !== 0) {
              index = i;
            }
            i += 1;
          }
          if (!index) { // If the line of text happens to fall on the first line and index is not set.
            // Check to see if markup has already been inserted and undo it.
            if (text.before.slice(0, markup.length) === markup) {
              newtext = text.before.substring(markup.length) + text.after;
              start = text.before.length - markup.length;
              end = text.before.length - markup.length;
              return insertMarkup(newtext, start, end);
            } else {
              newtext = markup + text.before.substring(0) + text.after;
              start = (text.before + markup).length;
              end = (text.before + markup).length;
              return insertMarkup(newtext, start, end);
            }
            // Check to see if markup has already been inserted and undo it.
          } else if (text.before.slice((index + 1), (index + 1 + markup.length)) === markup) {
            newtext = (
                text.before.substring(0, (index)) + "\n" +
                text.before.substring(index + 1 + markup.length) + text.after
                );
            start = text.before.length - markup.length;
            end = text.before.length - markup.length;
            return insertMarkup(newtext, start, end);
          } else {
            newtext = (
                text.before.substring(0, (index)) + "\n" +
                markup + text.before.substring(index + 1) + text.after
                );
            start = (text.before + markup).length;
            end = (text.before + markup).length;
            return insertMarkup(newtext, start, end);
          }
        }
      };

      scope.insertList = function() {
        return scope.applyBlockMarkup("* ");
      };

      scope.insertNumList = function() {
        return scope.applyBlockMarkup("1. ");
      };

      scope.insertQuote = function() {
        return scope.applyBlockMarkup("> ");
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
      var renderMathAndMarkdown = function(textToCheck) {
        var convert = $filter('converter');
        var re = /\$\$/g;

        var startMath = 0;
        var endMath = 0;

        var indexes = (function () {
          var match;
          var result = [];
          while (match = re.exec(textToCheck)) {
            result.push(match.index);
          }
          return result;
        })();
        indexes.push(textToCheck.length);

        var parts = (function () {
          var result = [];
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
          return result;
        })();

        var htmlString = parts.join('');

        // Transform the HTML string into a DOM element.
        var domElement = document.createElement('div');
        domElement.innerHTML = htmlString;

        mediaEmbedder.replaceLinksWithEmbeds(domElement);

        return domElement.innerHTML;
      };

      var renderInlineMath = function(textToCheck) {
        var re = /\\?\\\(|\\?\\\)/g;
        var startMath = null;
        var endMath = null;
        var match = undefined;
        var indexes = [];
        while (match = re.exec(textToCheck)) {
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

      // Re-render the markdown when the view needs updating.
      ctrl.$render = function() {
        if (!scope.readOnly && !scope.preview) {
          inputEl.val((ctrl.$viewValue || ''));
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
        return $timeout(function() {
          return ctrl.$setViewValue(inputEl.val());
        });
      });

      // Reset height of output div incase it has been changed.
      // Re-render when it becomes uneditable.
      // Auto-focus the input box when the widget becomes editable.
      return scope.$watch('readOnly', function(readOnly) {
        scope.preview = false;
        output.style.height = "";
        ctrl.$render();
        if (!readOnly) {
          return $timeout(function() { return input.focus(); });
        }
      });
    },

    require: '?ngModel',
    restrict: 'E',
    scope: {
      readOnly: '=',
      required: '@'
    },
    templateUrl: 'markdown.html'
  };
};
