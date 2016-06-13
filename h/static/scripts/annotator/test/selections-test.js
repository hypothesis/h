'use strict';

var unroll = require('../../test/util').unroll;

var observable = require('../../util/observable');
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
  var clock;
  var fakeDocument;
  var range;
  var rangeSub;
  var onSelectionChanged;

  beforeEach(function () {
    clock = sinon.useFakeTimers();
    fakeDocument = new FakeDocument();
    onSelectionChanged = sinon.stub();

    // Subscribe to selection changes, ignoring the initial event
    var ranges = observable.drop(selections(fakeDocument), 1);
    rangeSub = ranges.subscribe({next: onSelectionChanged});

    range = {};
    fakeDocument.selection = {
      rangeCount: 1,
      getRangeAt: function (index) {
        return index === 0 ? range : null;
      },
    };
  });

  afterEach(function () {
    rangeSub.unsubscribe();
    clock.restore();
  });

  unroll('emits the selected range when #event occurs', function (testCase) {
    fakeDocument.dispatchEvent({type: testCase.event});
    clock.tick(testCase.delay);
    assert.calledWith(onSelectionChanged, range);
  }, [
    {event: 'mouseup', delay: 20},
  ]);

  it('emits an event if there is a selection at the initial subscription', function () {
    var onInitialSelection = sinon.stub();
    var ranges = selections(fakeDocument);
    var sub = ranges.subscribe({next: onInitialSelection});
    clock.tick(1);
    assert.called(onInitialSelection);
    sub.unsubscribe();
  });

  describe('when the selection changes', function () {
    it('emits a selection if the mouse is not down', function () {
      fakeDocument.dispatchEvent({type: 'selectionchange'});
      clock.tick(200);
      assert.calledWith(onSelectionChanged, range);
    });

    it('does not emit a selection if the mouse is down', function () {
      fakeDocument.dispatchEvent({type: 'mousedown'});
      fakeDocument.dispatchEvent({type: 'selectionchange'});
      clock.tick(200);
      assert.notCalled(onSelectionChanged);
    });

    it('does not emit a selection until there is a pause since the last change', function () {
      fakeDocument.dispatchEvent({type: 'selectionchange'});
      clock.tick(90);
      fakeDocument.dispatchEvent({type: 'selectionchange'});
      clock.tick(90);
      assert.notCalled(onSelectionChanged);
      clock.tick(20);
      assert.called(onSelectionChanged);
    });
  });
});
