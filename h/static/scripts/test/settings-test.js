var settings = require('../settings');

function createJSONScriptTag(obj) {
  var el = document.createElement('script');
  el.type = 'application/json';
  el.textContent = JSON.stringify(obj);
  el.classList.add('js-hypothesis-settings');
  return el;
}

describe('settings', function () {
  afterEach(function () {
    var elements = document.querySelectorAll('.js-hypothesis-settings');
    for (var i=0; i < elements.length; i++) {
      elements[i].parentNode.removeChild(elements[i]);
    }
  });

  it('should merge settings', function () {
    document.body.appendChild(createJSONScriptTag({ a: 1 }));
    document.body.appendChild(createJSONScriptTag({ b: 2 }));
    assert.deepEqual(settings(document), { a: 1, b: 2 });
  });
});
