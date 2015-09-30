var fetch = require('isomorphic-fetch');
var swig = require('swig');

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

// fetch the text for Karma resource which matches the given regex.
// The resource must have been included in the list of files for the test
// specified in the karma.config.js file
function fetchTemplate(pathRegex) {
  var templateUrl = Object.keys(window.__karma__.files).filter(function (path) {
    return path.match(pathRegex);
  })[0];
  return fetch(templateUrl).then(function (response) {
    return response.text();
  });
}

describe('CreateGroupFormController', function () {
  var element;
  var template;

  before(function () {
    return fetchTemplate(/create\.html\.jinja2$/).then(function (text) {
      // extract the 'content' block from the template
      var contentBlock = text.match(/{% block content %}([^]*){% endblock content %}/)[1];
      template = swig.compile(contentBlock);
    });
  });

  beforeEach(function () {
    var context = {
      form: {
        csrf_token: {
          render: function() {}
        },
        name: ''
      }
    };
    element = document.createElement('div');
    element.innerHTML = template(context);
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
