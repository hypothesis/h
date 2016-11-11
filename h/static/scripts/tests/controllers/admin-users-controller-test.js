'use strict';

var AdminUsersController = require('../../controllers/admin-users-controller');

function submitEvent() {
  return new Event('submit', {bubbles: true, cancelable: true});
}

describe('AdminUsersController', () => {
  var root;
  var form;

  beforeEach(() => {
    root = document.createElement('div');
    root.innerHTML = '<form><input type="submit"></form>';
    form = root.querySelector('form');
    document.body.appendChild(root);
  });

  afterEach(() => {
    root.remove();
  });

  it('it submits the form when confirm returns true', () => {
    var event = submitEvent();
    var fakeWindow = {confirm: sinon.stub().returns(true)};
    new AdminUsersController(root, {window: fakeWindow});

    form.dispatchEvent(event);

    assert.isFalse(event.defaultPrevented);
  });

  it('it cancels the form submission when confirm returns false', () => {
    var event = submitEvent();
    var fakeWindow = {confirm: sinon.stub().returns(false)};
    new AdminUsersController(root, {window: fakeWindow});

    form.dispatchEvent(event);

    assert.isTrue(event.defaultPrevented);
  });
});
