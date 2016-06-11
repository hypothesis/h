'use strict';

/**
 * Functions (aka. 'operators') for generating and manipulating streams of
 * values using the Observable API.
 */

var Observable = require('zen-observable');

 /**
  * Returns an observable of events emitted by a DOM event source
  * (eg. an Element, Document or Window).
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

/** Drop the first `n` events from the `src` Observable. */
function drop(src, n) {
  var count = 0;
  return src.filter(function () {
    ++count;
    return count > n;
  });
}

module.exports = {
  buffer: buffer,
  drop: drop,
  listen: listen,
  merge: merge,
  Observable: Observable,
};
