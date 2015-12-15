var showdown = require('showdown');

function targetBlank(converter) {
  function filter(text) {
    return text.replace(/<a href=/g, '<a target="_blank" href=');
  }
  return [{type: 'output', filter: filter}];
}

module.exports = function () {
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
  return converter.makeHtml.bind(converter);
};
