var Markdown = require('../vendor/Markdown.Converter');

function Converter() {
  Markdown.Converter.call(this);
  this.hooks.chain('preConversion', function (text) {
    return text || '';
  });
  this.hooks.chain('postConversion', function (text) {
    return text.replace(/<a href=/g, "<a target=\"_blank\" href=");
  });
}

module.exports = function () {
  return (new Converter()).makeHtml;
};
