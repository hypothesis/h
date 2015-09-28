var converter = require('../converter');

describe('markdown converter', function () {
  var markdownToHTML = converter();
  it('should autolink URLs', function () {
    assert.equal(markdownToHTML('See this link - http://arxiv.org/article'),
      '<p>See this link - <a target="_blank" href="http://arxiv.org/article">' +
      'http://arxiv.org/article</a></p>');
  });
});
