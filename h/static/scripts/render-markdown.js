'use strict';

var katex = require('katex');
var showdown = require('showdown');

function targetBlank() {
  function filter(text) {
    return text.replace(/<a href=/g, '<a target="_blank" href=');
  }
  return [{type: 'output', filter: filter}];
}

function renderMarkdown(html) {
  // see https://github.com/showdownjs/showdown#valid-options
  var converter = new showdown.Converter({
    extensions: [targetBlank],
    simplifiedAutoLink: true,
    // Since we're using simplifiedAutoLink we also use
    // literalMidWordUnderscores because otherwise _'s in URLs get
    // transformed into <em>'s.
    // See https://github.com/showdownjs/showdown/issues/211
    literalMidWordUnderscores: true,
  });
  return converter.makeHtml(html);
}

function renderInlineMath(textToCheck, $sanitize) {
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
        $sanitize(textToCheck.substring(startMath, endMath));
      }
    }
  }
  return textToCheck;
}

function renderMathAndMarkdown(textToCheck, $sanitize) {
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
            return $sanitize(textToCheck.substring(startMath, index));
          }
        } else {
          startMath = index + 2;
          return $sanitize(renderMarkdown(renderInlineMath(textToCheck.substring(endMath, index), $sanitize)));
        }
      })());
    }
    /* jshint +W083 */
    return result;
  })();

  return parts.join('');
}

module.exports = renderMathAndMarkdown;
