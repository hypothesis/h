'use strict';

var page = require('../page');

// helper to dispatch a native event to an element
function sendEvent(element, eventType) {
  // createEvent() used instead of Event constructor
  // for PhantomJS compatibility
  var event = document.createEvent('Event');
  event.initEvent(eventType, true /* bubbles */, true /* cancelable */);
  element.dispatchEvent(event);

  return event;
}

describe('page', function () {
  it('it adds the callback when the url path matches', function () {
    var spy = sinon.spy();

    page(document.location.pathname, spy);
    sendEvent(document, 'DOMContentLoaded');

    assert.calledOnce(spy);
  });

  it('it skips adding the callback when the url path does not match', function () {
    var spy = sinon.spy();

    page(document.location.pathname + '-foo', spy);
    sendEvent(document, 'DOMContentLoaded');

    assert.notCalled(spy);
  });
});
