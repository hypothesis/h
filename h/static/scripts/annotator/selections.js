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
 * Returns an observable of `DOMRange` for the selection in the given
 * @p document.
 *
 * @return Observable<DOMRange|null>
 */
function selections(document, setTimeout, clearTimeout) {
  setTimeout = setTimeout || window.setTimeout;
  clearTimeout = clearTimeout || window.clearTimeout;

  var events = listen(document, ['ready', 'mouseup']);
  return new Observable(function (obs) {
    function emitRange() {
      var selection = document.getSelection();
      if (!selection.rangeCount || selection.getRangeAt(0).collapsed) {
        obs.next(null);
      } else {
        obs.next(selection.getRangeAt(0));
      }
    }

    var timeout;
    var sub = events.subscribe({
      next: function () {
        // Add a delay before checking the state of the selection because
        // the selection is not updated immediately after a 'mouseup' event
        // but only on the next tick of the event loop.
        timeout = setTimeout(emitRange, 0);
      },
    });

    return function () {
      clearTimeout(timeout);
      sub.unsubscribe();
    };
  });
}

module.exports = selections;
