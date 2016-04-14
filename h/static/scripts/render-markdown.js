'use strict';

var katex = require('katex');
var showdown = require('showdown');

function targetBlank() {
  function filter(text) {
    return text.replace(/<a href=/g, '<a target="_blank" href=');
  }
  return [{type: 'output', filter: filter}];
}

var converter;

/**
 * Render markdown to HTML.
 *
 * This function does *not* sanitize the HTML in any way, that is the caller's
 * responsibility.
 */
function renderMarkdown(markdown) {
  if (!converter) {
    // see https://github.com/showdownjs/showdown#valid-options
    converter = new showdown.Converter({
      extensions: [targetBlank],
      simplifiedAutoLink: true,
      // Since we're using simplifiedAutoLink we also use
      // literalMidWordUnderscores because otherwise _'s in URLs get
      // transformed into <em>'s.
      // See https://github.com/showdownjs/showdown/issues/211
      literalMidWordUnderscores: true,
    });
  }
  return converter.makeHtml(markdown);
}

/**
 * Replaces inline math between '\(' and '\)' delimiters
 * with math rendered by KaTeX.
 */
function renderInlineMath(text) {
  var mathStart = text.indexOf('\\(');
  if (mathStart !== -1) {
    var mathEnd = text.indexOf('\\)', mathStart);
    if (mathEnd !== -1) {
      var markdownSection = text.slice(0, mathStart);
      var mathSection = text.slice(mathStart + 2, mathEnd);
      var renderedMath = katex.renderToString(mathSection);
      return markdownSection +
             renderedMath +
             renderInlineMath(text.slice(mathEnd + 2));
    }
  }
  return text;
}

/**
 * Renders mixed blocks of markdown and LaTeX to HTML.
 *
 * LaTeX blocks are delimited by '$$' (for blocks) or '\(' and '\)'
 * (for inline math).
 *
 * @param {string} text - The markdown and LaTeX to render
 * @param {(string) => string} $sanitize - A function that sanitizes HTML to
 *        remove any potentially unsafe tokens (eg. <script> tags).
 * @return {string} The sanitized HTML
 */
function renderMathAndMarkdown(text, $sanitize) {
  var html = text.split('$$').map(function (part, index) {
    if (index % 2 === 0) {
      // Plain markdown block
      return renderMarkdown(renderInlineMath(part));
    } else {
      // Math block
      try {
        // \\displaystyle tells KaTeX to render the math in display style
        // (full sized fonts).
        return katex.renderToString("\\displaystyle {" + part + "}");
      } catch (error) {
        return part;
      }
    }
  }).join('');

  return $sanitize(html);
}

module.exports = renderMathAndMarkdown;
