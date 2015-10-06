"use strict";

var CreateGroupFormController = require('../create-group-form');

function isHidden(elt) {
  return elt.classList.contains('is-hidden');
}

// helper to dispatch a native event to an element
function sendEvent(element, eventType) {
  // createEvent() used instead of Event constructor
  // for PhantomJS compatibility
  var event = document.createEvent('Event');
  event.initEvent(eventType, true /* bubbles */, true /* cancelable */);
  element.dispatchEvent(event);
}

describe('CreateGroupFormController', function () {
  var element;
  var template;

  before(function () {
    template = '<input type="text" class="js-group-name-input">' +
               '<input type="submit" class="js-create-group-create-btn">' +
               '<a href="" class="js-group-info-link">Tell me more!</a>' +
               '<div class="js-group-info-text is-hidden">More!</div>';
  });

  beforeEach(function () {
    element = document.createElement('div');
    element.innerHTML = template;
  });

  it('should enable submission if form is valid', function () {
    var controller = new CreateGroupFormController(element);
    controller._groupNameInput.value = '';
    sendEvent(controller._groupNameInput, 'input');
    assert.equal(controller._submitBtn.disabled, true);
    controller._groupNameInput.value = 'a group name';
    sendEvent(controller._groupNameInput, 'input');
    assert.equal(controller._submitBtn.disabled, false);
  });

  it('should toggle info text when explain link is clicked', function () {
    var controller = new CreateGroupFormController(element);
    assert.equal(isHidden(controller._infoText), true);
    sendEvent(controller._infoLink, 'click');
    assert.equal(isHidden(controller._infoText), false);
    assert.equal(isHidden(controller._infoLink), true);
  });
});
