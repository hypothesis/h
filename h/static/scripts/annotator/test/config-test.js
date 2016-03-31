'use strict';

var config = require('../config');

describe('annotator configuration', function () {
  var fakeScriptConfig;

  function fakeQuerySelector(selector) {
    if (selector === 'link[type="application/annotator+html"]') {
      return {href: 'app.html'};
    } else if (selector === 'script.js-hypothesis-config' &&
               fakeScriptConfig) {
      return {textContent: fakeScriptConfig};
    } else {
      return null;
    }
  }

  var fakeWindowBase = {
    document: {
      querySelector: fakeQuerySelector,
      querySelectorAll: function (selector) {
        var match = fakeQuerySelector(selector);
        return match ? [match] : [];
      },
    },
    location: {hash: ''},
  };

  beforeEach(function () {
    fakeScriptConfig = '';
  });

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
      location: {href:'https://foo.com/#annotations:456'},
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

  it('merges the config from the "hypothesis-config" meta tag', function () {
    fakeScriptConfig = '{"annotations":"456"}';
    assert.deepEqual(config(fakeWindowBase), {
      app: 'app.html',
      annotations: '456',
    });
  });
});
