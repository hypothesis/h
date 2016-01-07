var detectContentType = require('../lib/detect-content-type');

describe('detectContentType()', function () {
  var el;
  beforeEach(function () {
    el = document.createElement('div');
    document.body.appendChild(el);
  });

  afterEach(function () {
    el.parentElement.removeChild(el);
  });

  it('returns HTML by default', function () {
    el.innerHTML = '<div></div>';
    assert.deepEqual(detectContentType(), { type: 'HTML' } );
  });

  it('returns "PDF" if the Chrome PDF plugin is present', function () {
    el.innerHTML =
     '<embed name="plugin" id="plugin" type="application/pdf"></embed>';
    assert.deepEqual(detectContentType(), { type: 'PDF' });
  });
});
