import { renderMathAndMarkdown, $imports } from '../render-markdown';

describe('render-markdown', () => {
  let render;

  beforeEach(() => {
    $imports.$mock({
      katex: {
        default: {
          renderToString: function (input, opts) {
            if (opts && opts.displayMode) {
              return 'math+display:' + input;
            } else {
              return 'math:' + input;
            }
          },
        },
      },
    });

    render = markdown => renderMathAndMarkdown(markdown);
  });

  afterEach(() => {
    $imports.$restore();
  });

  describe('autolinking', () => {
    it('should autolink URLs', () => {
      assert.equal(
        render('See this link - http://arxiv.org/article'),
        '<p>See this link - <a href="http://arxiv.org/article" target="_blank">' +
          'http://arxiv.org/article</a></p>',
      );
    });

    it("should autolink URLs with _'s in them correctly", () => {
      assert.equal(
        render(
          'See this https://hypothes.is/stream?q=tag:group_test_needs_card',
        ),
        '<p>See this <a ' +
          'href="https://hypothes.is/stream?q=tag:group_test_needs_card" ' +
          'target="_blank">' +
          'https://hypothes.is/stream?q=tag:group_test_needs_card</a></p>',
      );
    });

    ['.', ',', '!', '?'].forEach(symbol => {
      it('should autolink URLs excluding trailing punctuation symbols', () => {
        assert.equal(
          render(`See this link - http://arxiv.org/article${symbol}`),
          '<p>See this link - <a href="http://arxiv.org/article" target="_blank">' +
            `http://arxiv.org/article</a>${symbol}</p>`,
        );
      });
    });
  });

  describe('markdown rendering', () => {
    it('should render markdown', () => {
      assert.equal(
        render('one **two** three'),
        '<p>one <strong>two</strong> three</p>',
      );
    });

    it('should sanitize the result', () => {
      // Check that the rendered HTML is fed through the HTML sanitization
      // library. This is not an extensive test of sanitization behavior, that
      // is left to DOMPurify's tests.
      assert.equal(
        renderMathAndMarkdown('one **two** <script>alert("three")</script>'),
        '<p>one <strong>two</strong> </p>',
      );
    });

    it('should open links in a new window', () => {
      assert.equal(
        renderMathAndMarkdown('<a href="http://example.com">test</a>'),
        '<p><a href="http://example.com" target="_blank">test</a></p>',
      );
    });

    it('should render strikethrough', () => {
      assert.equal(
        renderMathAndMarkdown('This is ~~no longer the case~~'),
        '<p>This is <del>no longer the case</del></p>',
      );
    });
  });

  describe('math blocks', () => {
    it('should render LaTeX blocks', () => {
      assert.equal(render('$$x*2$$'), '<p>math+display:x*2</p>');
    });

    it('should render mixed blocks', () => {
      assert.equal(
        render('one $$x*2$$ two $$x*3$$ three'),
        '<p>one </p>\n<p>math+display:x*2</p>\n' +
          '<p>two </p>\n<p>math+display:x*3</p>\n<p>three</p>',
      );
    });

    it('should not sanitize math renderer output', () => {
      // Check that KaTeX's rendered output is not corrupted in any way by
      // sanitization.
      const html = render('$$ <unknown-tag>foo</unknown-tag> $$');
      assert.include(html, '<unknown-tag>foo</unknown-tag>');
    });

    it('should render mixed inline and block math', () => {
      assert.equal(
        render('one \\(x*2\\) three $$x*3$$'),
        '<p>one math:x*2 three </p>\n<p>math+display:x*3</p>',
      );
    });
  });

  describe('inline math', () => {
    it('should render inline LaTeX', () => {
      assert.equal(render('\\(x*2\\)'), '<p>math:x*2</p>');
    });

    it('should render mixed inline LaTeX blocks', () => {
      assert.equal(
        render('one \\(x+2\\) two \\(x+3\\) four'),
        '<p>one math:x+2 two math:x+3 four</p>',
      );
    });
  });
});
