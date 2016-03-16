'use strict';

var config = require('../config');

describe('annotator configuration', function () {
  var fakeWindowBase = {
    document: {
      querySelector: sinon.stub().returns({href: 'app.html'}),
    },
    location: {hash: ''},
  };

  it('reads the app src from the link tag', function () {
    var linkEl = document.createElement('link');
    linkEl.type = 'application/annotator+html';
    linkEl.href = 'https://test.hypothes.is/app.html';
    document.head.appendChild(linkEl);
    assert.deepEqual(config(window), {
      app: linkEl.href,
    });
    document.head.removeChild(linkEl);
  });

  it('reads the #annotation query fragment', function () {
    var fakeWindow = Object.assign({}, fakeWindowBase, {
      location: {hash:'#annotations:456'},
    });
    assert.deepEqual(config(fakeWindow), {
      app: 'app.html',
      annotations: '456',
    });
  });

  it('merges the config from hypothesisConfig()', function () {
    var fakeWindow = Object.assign({}, fakeWindowBase, {
      hypothesisConfig: function () {
        return {firstRun: true};
      },
    });
    assert.deepEqual(config(fakeWindow), {
      app: 'app.html',
      firstRun: true,
    });
  });
});
