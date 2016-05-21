'use strict';

var unroll = require('../../test/util').unroll;

var selections = require('../selections');

function FakeDocument() {
  var listeners = {};

  return {
    getSelection: function () {
      return this.selection;
    },

    addEventListener: function (name, listener) {
      listeners[name] = (listeners[name] || []).concat(listener);
    },

    removeEventListener: function (name, listener) {
      listeners[name] = listeners[name].filter(function (lis) {
        return lis !== listener;
      });
    },

    dispatchEvent: function (event) {
      listeners[event.type].forEach(function (fn) { fn(event); });
    },
  };
}

describe('selections', function () {
  var fakeDocument;
  var rangeSub;
  var onSelectionChanged;

  beforeEach(function () {
    fakeDocument = new FakeDocument();
    onSelectionChanged = sinon.stub();

    var fakeSetTimeout = function (fn) { fn(); };
    var fakeClearTimeout = function () {};

    var ranges = selections(fakeDocument, fakeSetTimeout, fakeClearTimeout);
    rangeSub = ranges.subscribe({next: onSelectionChanged});
  });

  afterEach(function () {
    rangeSub.unsubscribe();
  });

  unroll('emits the selected range when #event occurs', function (testCase) {
    var range = {};
    fakeDocument.selection = {
      rangeCount: 1,
      getRangeAt: function (index) {
        return index === 0 ? range : null;
      },
    };
    fakeDocument.dispatchEvent({type: testCase.event});
    assert.calledWith(onSelectionChanged, range);
  }, [{event: 'mouseup'}, {event: 'ready'}]);
});
