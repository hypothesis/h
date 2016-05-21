'use strict';

var Observable = require('zen-observable');

/**
 * Returns an observable of events emitted by `src`.
 *
 * @param {EventTarget} src - The event source.
 * @param {Array<string>} eventNames - List of events to subscribe to
 */
function listen(src, eventNames) {
  return new Observable(function (observer) {
    var onNext = function (event) {
      observer.next(event);
    };

    eventNames.forEach(function (event) {
      src.addEventListener(event, onNext);
    });

    return function () {
      eventNames.forEach(function (event) {
        src.removeEventListener(event, onNext);
      });
    };
  });
}

/**
 * Buffers events from a source Observable, waiting for a pause of `delay`
 * ms with no events before emitting the last value from `src`.
 *
 * @param {number} delay
 * @param {Observable<T>} src
 * @return {Observable<T>}
 */
function buffer(delay, src) {
  return new Observable(function (obs) {
    var lastValue;
    var timeout;

    function onNext() {
      obs.next(lastValue);
    }

    var sub = src.subscribe({
      next: function (value) {
        lastValue = value;
        clearTimeout(timeout);
        timeout = setTimeout(onNext, delay);
      }
    });

    return function () {
      sub.unsubscribe();
      clearTimeout(timeout);
    };
  });
}

/**
 * Merges multiple streams of values into a single stream.
 *
 * @param {Array<Observable>} sources
 * @return Observable
 */
function merge(sources) {
  return new Observable(function (obs) {
    var subs = sources.map(function (src) {
      return src.subscribe({
        next: function (value) {
          obs.next(value);
        },
      });
    });

    return function () {
      subs.forEach(function (sub) {
        sub.unsubscribe();
      });
    };
  });
}

/**
 * Returns an observable of `DOMRange` for the selection in the given
 * @p document.
 *
 * The returned stream will emit `null` when the selection is empty.
 *
 * @return Observable<DOMRange|null>
 */
function selections(document) {

  // Get a stream of selection changes that occur whilst the user is not
  // making a selection with the mouse.
  var isMouseDown;
  var selectionEvents = listen(document, ['mousedown', 'mouseup', 'selectionchange'])
  .filter(function (event) {
    if (event.type === 'mousedown' || event.type === 'mouseup') {
      isMouseDown = event.type === 'mousedown';
      return false;
    } else {
      return !isMouseDown;
    }
  });

  var events = merge([
    // Add a delay before checking the state of the selection because
    // the selection is not updated immediately after a 'mouseup' event
    // but only on the next tick of the event loop.
    buffer(10, listen(document, ['ready', 'mouseup'])),

    // Buffer selection changes to avoid continually emitting events whilst the
    // user drags the selection handles on mobile devices
    buffer(100, selectionEvents),
  ]);

  return events.map(function () {
    var selection = document.getSelection();
    if (!selection.rangeCount || selection.getRangeAt(0).collapsed) {
      return null;
    } else {
      return selection.getRangeAt(0);
    }
  });
}

module.exports = selections;
