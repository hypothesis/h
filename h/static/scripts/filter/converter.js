var showdown = require('showdown');

function targetBlank(converter) {
  function filter(text) {
    return text.replace(/<a href=/g, '<a target="_blank" href=');
  }
  return [{type: 'output', filter: filter}];
}

module.exports = function () {
  var converter = new showdown.Converter({extensions: [targetBlank]});
  return converter.makeHtml.bind(converter);
};
