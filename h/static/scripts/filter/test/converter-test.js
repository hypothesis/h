var converter = require('../converter');

describe('markdown converter', function () {
  var markdownToHTML = converter();

  it('should autolink URLs', function () {
    assert.equal(markdownToHTML('See this link - http://arxiv.org/article'),
      '<p>See this link - <a target="_blank" href="http://arxiv.org/article">' +
      'http://arxiv.org/article</a></p>');
  });

  it('should autolink URLs with _\'s in them correctly', function () {
    assert.equal(
      markdownToHTML(
        'See this https://hypothes.is/stream?q=tag:group_test_needs_card'),
      '<p>See this <a target="_blank" ' +
      'href="https://hypothes.is/stream?q=tag:group_test_needs_card">' +
      'https://hypothes.is/stream?q=tag:group_test_needs_card</a></p>');
  });
});
