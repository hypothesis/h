// Tests that annotated sections of the page are correctly highlighted when
// annotations are loaded via the bridge that connects the sidebar app and the
// annotator guest.

'use strict';

var Annotator = require('annotator');

var unroll = require('../../../test/util').unroll;
var Guest = require('../../guest');

function quoteSelector(quote) {
  return {
    type: 'TextQuoteSelector',
    exact: quote,
  };
}

/** Generate an annotation that matches a text quote in a page. */
function annotateQuote(quote) {
  return {
    target: [{
      selector: [quoteSelector(quote)],
    }],
  };
}

/**
 * Return the text of all highlighted phrases in `container`.
 *
 * @param {Element} container
 */
function highlightedPhrases(container) {
  return Array.from(container.querySelectorAll('.annotator-hl')).map(function (el) {
    return el.textContent;
  });
}

function simplifyWhitespace(quote) {
  return quote.replace(/\s+/g, ' ');
}

function FakeCrossFrame(elem, options) {
  var waiters = [];

  this.destroy = sinon.stub();
  this.onConnect = sinon.stub();
  this.on = sinon.stub();
  this.options = options;

  this.sync = function () {
    waiters.forEach(function (waiter) {
      --waiter.count;
      if (waiter.count === 0) {
        waiter.resolve();
        waiters = waiters.filter(function (w) {
          return w !== waiter;
        });
      }
    });
  };

  /** Wait for `count` annotations to be anchored. */
  this.awaitSync = function (count) {
    return new Promise(function (resolve) {
      waiters.push({
        count: count,
        resolve: resolve,
      });
    });
  };
}

describe('anchoring', function () {
  var guest;
  var container;
  var crossFrame;

  before(function () {
    Annotator.Plugin.CrossFrame = FakeCrossFrame;
  });

  beforeEach(function () {
    container = document.createElement('div');
    container.innerHTML = require('./test-page.html');
    document.body.appendChild(container);
    guest = new Guest(container);
    crossFrame = guest.crossframe;
  });

  afterEach(function () {
    guest.destroy();
    container.parentNode.removeChild(container);
  });

  unroll('should highlight #tag when annotations are loaded', function (testCase) {
    var normalize = function (quotes) {
      return quotes.map(function (q) { return simplifyWhitespace(q); });
    };

    var annotations = testCase.quotes.map(function (q) {
      return annotateQuote(q);
    });

    // Simulate new annotations being loaded via the bridge
    crossFrame.options.emit('annotationsLoaded', annotations);

    return crossFrame.awaitSync(testCase.quotes.length).then(function () {
      var assertFn = testCase.expectFail ? assert.notDeepEqual : assert.deepEqual;
      assertFn(normalize(highlightedPhrases(container)),
               normalize(testCase.quotes));
    });
  }, [{
    tag: 'a simple quote',
    quotes: ['This has not been a scientist\'s war'],
  },{
    // Known failure with nested annotations that are anchored via quotes
    // or positions. See https://github.com/hypothesis/h/pull/3313 and
    // https://github.com/hypothesis/h/issues/3278
    tag: 'nested quotes',
    quotes: [
      'This has not been a scientist\'s war;' +
        ' it has been a war in which all have had a part',
      'scientist\'s war',
    ],
    expectFail: true,
  }]);
});
