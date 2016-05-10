'use strict';

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

  it('returns "PDF" if Google Chrome PDF viewer is present', function () {
    el.innerHTML = '<embed name="plugin" type="application/pdf"></embed>';
    assert.deepEqual(detectContentType(), { type: 'PDF' });
  });

  it('returns "PDF" if Firefox PDF viewer is present', function () {
    var fakeDocument = {
      querySelector: function () { return null; },
      baseURI: 'resource://pdf.js',
    };
    assert.deepEqual(detectContentType(fakeDocument), { type: 'PDF' });
  });
});
