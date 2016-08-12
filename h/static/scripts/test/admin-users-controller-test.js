'use strict';

var AdminUsersController = require('../controllers/admin-users-controller');

// helper to dispatch a native event to an element
function sendEvent(element, eventType) {
  // createEvent() used instead of Event constructor
  // for PhantomJS compatibility
  var event = document.createEvent('Event');
  event.initEvent(eventType, true /* bubbles */, true /* cancelable */);
  element.dispatchEvent(event);

  return event;
}

describe('AdminUsersController', function () {
  var root;
  var form;

  beforeEach(function () {
    root = document.createElement('div');
    root.innerHTML = '<form id="js-users-delete-form">' +
                     '<input type="submit" id="submit-btn">';
    form = root.querySelector('form');
    document.body.appendChild(root);
  });

  afterEach(function () {
    root.parentNode.removeChild(root);
  });

  it('it submits the form when confirm returns true', function () {
    var fakeWindow = {confirm: sinon.stub().returns(true)};
    new AdminUsersController(root, fakeWindow);

    var event = sendEvent(form, 'submit');
    assert.isFalse(event.defaultPrevented);
  });

  it('it cancels the form submission when confirm returns false', function () {
    var fakeWindow = {confirm: sinon.stub().returns(false)};
    new AdminUsersController(root, fakeWindow);

    var event = sendEvent(form, 'submit');
    assert.isTrue(event.defaultPrevented);
  });
});
