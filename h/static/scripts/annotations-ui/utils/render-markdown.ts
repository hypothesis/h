import createDOMPurify from 'dompurify';
import escapeHtml from 'escape-html';
import katex from 'katex';
import showdown from 'showdown';

const DOMPurify = createDOMPurify(window);

// Ensure that any links generated either by Showdown or in the markdown/HTML
// passed to Showdown open in an external window.
DOMPurify.addHook('afterSanitizeAttributes', node => {
  if ('target' in node) {
    node.setAttribute('target', '_blank');
  }
});

function targetBlank() {
  function filter(text: string) {
    return text.replace(/<a href=/g, '<a target="_blank" href=');
  }
  return [{ type: 'output', filter }];
}

let converter: showdown.Converter;

function renderMarkdown(markdown: string) {
  if (!converter) {
    // see https://github.com/showdownjs/showdown#valid-options
    converter = new showdown.Converter({
      extensions: [targetBlank],
      simplifiedAutoLink: true,
      excludeTrailingPunctuationFromURLs: true,
      // Since we're using simplifiedAutoLink we also use
      // literalMidWordUnderscores because otherwise _'s in URLs get
      // transformed into <em>'s.
      // See https://github.com/showdownjs/showdown/issues/211
      literalMidWordUnderscores: true,
      // Enable strikethrough, which is disabled by default
      strikethrough: true,
    });
  }
  return converter.makeHtml(markdown);
}

function mathPlaceholder(id: number) {
  return '{math:' + id.toString() + '}';
}

type MathBlock = {
  id: number;
  inline: boolean;
  expression: string;
};

/**
 * Parses a string containing mixed markdown and LaTeX in between
 * '$$..$$' or '\( ... \)' delimiters and returns an object containing a
 * list of math blocks found in the string, plus the input string with math
 * blocks replaced by placeholders.
 */
function extractMath(content: string): {
  content: string;
  mathBlocks: MathBlock[];
} {
  const mathBlocks: MathBlock[] = [];
  let pos = 0;
  let replacedContent = content;

  while (true) {
    const blockMathStart = replacedContent.indexOf('$$', pos);
    const inlineMathStart = replacedContent.indexOf('\\(', pos);

    if (blockMathStart === -1 && inlineMathStart === -1) {
      break;
    }

    let mathStart;
    let mathEnd;
    if (
      blockMathStart !== -1 &&
      (inlineMathStart === -1 || blockMathStart < inlineMathStart)
    ) {
      mathStart = blockMathStart;
      mathEnd = replacedContent.indexOf('$$', mathStart + 2);
    } else {
      mathStart = inlineMathStart;
      mathEnd = replacedContent.indexOf('\\)', mathStart + 2);
    }

    if (mathEnd === -1) {
      break;
    } else {
      mathEnd = mathEnd + 2;
    }

    const id = mathBlocks.length + 1;
    const placeholder = mathPlaceholder(id);
    mathBlocks.push({
      id,
      expression: replacedContent.slice(mathStart + 2, mathEnd - 2),
      inline: inlineMathStart !== -1,
    });

    let replacement;
    if (inlineMathStart !== -1) {
      replacement = placeholder;
    } else {
      // Add new lines before and after math blocks so that they render
      // as separate paragraphs
      replacement = '\n\n' + placeholder + '\n\n';
    }

    replacedContent =
      replacedContent.slice(0, mathStart) +
      replacement +
      replacedContent.slice(mathEnd);
    pos = mathStart + replacement.length;
  }

  return {
    mathBlocks,
    content: replacedContent,
  };
}

function insertMath(html: string, mathBlocks: MathBlock[]) {
  return mathBlocks.reduce((html, block) => {
    let renderedMath;
    try {
      if (block.inline) {
        renderedMath = katex.renderToString(block.expression);
      } else {
        renderedMath = katex.renderToString(block.expression, {
          displayMode: true,
        });
      }
    } catch {
      renderedMath = escapeHtml(block.expression);
    }
    return html.replace(mathPlaceholder(block.id), renderedMath);
  }, html);
}

/**
 * Convert a string of markdown and math into sanitized HTML.
 *
 * Math expressions in the input are written as LaTeX and must be enclosed in
 * `$$ .. $$` or `\( .. \)` delimiters to indicate block or inline math
 * expressions. These expressions are extracted and rendered using KaTeX.
 *
 * @return - A string of sanitized HTML.
 */
export function renderMathAndMarkdown(markdown: string): string {
  // KaTeX takes care of escaping its input, so we want to avoid passing its
  // output through the HTML sanitizer. Therefore we first extract the math
  // blocks from the input, render and sanitize the remaining markdown and then
  // render and re-insert the math blocks back into the output.
  const mathInfo = extractMath(markdown);
  const markdownHTML = DOMPurify.sanitize(renderMarkdown(mathInfo.content));
  const mathAndMarkdownHTML = insertMath(markdownHTML, mathInfo.mathBlocks);
  return mathAndMarkdownHTML;
}
