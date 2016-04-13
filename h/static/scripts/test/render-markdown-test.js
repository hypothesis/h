'use strict';

var proxyquire = require('proxyquire');

describe('render-markdown', function () {
  var render;
  var renderMarkdown;

  beforeEach(function () {
    renderMarkdown = proxyquire('../render-markdown', {
      katex: {
        renderToString: function (input) {
          return 'math:' + input;
        },
      },
    });
    render = function (markdown) {
      return renderMarkdown(markdown, function (html) { return html; });
    };
  });

  describe('autolinking', function () {
    it('should autolink URLs', function () {
      assert.equal(render('See this link - http://arxiv.org/article'),
        '<p>See this link - <a target="_blank" href="http://arxiv.org/article">' +
        'http://arxiv.org/article</a></p>');
    });

    it('should autolink URLs with _\'s in them correctly', function () {
      assert.equal(
        render(
          'See this https://hypothes.is/stream?q=tag:group_test_needs_card'),
        '<p>See this <a target="_blank" ' +
        'href="https://hypothes.is/stream?q=tag:group_test_needs_card">' +
        'https://hypothes.is/stream?q=tag:group_test_needs_card</a></p>');
    });
  });

  describe('markdown rendering', function () {
    it('should render markdown', function () {
      assert.equal(render('one **two** three'),
        '<p>one <strong>two</strong> three</p>');
    });

    it('should sanitize the result', function () {
      var sanitize = function (html) {
        return '<safe>' + html + '</safe>';
      };
      assert.equal(renderMarkdown('one **two** three', sanitize),
        '<safe><p>one <strong>two</strong> three</p></safe>');
    });
  });

  describe('math blocks', function () {
    it('should render LaTeX blocks', function () {
      assert.equal(render('$$x*2$$'), 'math:\\displaystyle {x*2}');
    });

    it('should render mixed blocks', function () {
      assert.equal(render('one $$x*2$$ two $$x*3$$ three'),
        '<p>one </p>math:\\displaystyle {x*2}<p>two </p>' +
        'math:\\displaystyle {x*3}<p>three</p>');
    });
  });

  describe('inline math', function () {
    it('should render inline LaTeX', function () {
      assert.equal(render('\\(x*2\\)'), '<p>math:x*2</p>');
    });

    it('should render mixed inline LaTeX blocks', function () {
      assert.equal(render('one \\(x+2\\) two \\(x+3\\) four'),
        '<p>one math:x+2 two math:x+3 four</p>');
    });
  });
});
