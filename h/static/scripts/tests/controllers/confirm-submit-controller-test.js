'use strict';

const ConfirmSubmitController = require('../../controllers/confirm-submit-controller');
const util = require('./util');

describe('ConfirmSubmitController', () => {

  let ctrl;

  afterEach(() => {
    if (ctrl) {
      ctrl.element.remove();
      ctrl = null;
    }
  });

  /**
   * Make a <button type="submit"> with the confirm submit controller
   * enhancement applied and return the various parts of the component.
   *
   */
  function component(windowConfirmReturnValue) {
    const confirmMessage = "Are you sure you want to leave the group 'Test Group'?";
    const template = `<button type="submit"
      class="js-confirm-submit"
      data-confirm-message="${confirmMessage}">
    `;

    const fakeWindow = {
      confirm: sinon.stub().returns(windowConfirmReturnValue),
    };

    ctrl = util.setupComponent(document,
                               template,
                               ConfirmSubmitController,
                               {window: fakeWindow});

    return {
      ctrl: ctrl,
      fakeWindow: fakeWindow,
      confirmMessage: confirmMessage,
    };
  }

  function fakeEvent() {
    const event = new Event('click');
    event.preventDefault = sinon.stub();
    event.stopPropagation = sinon.stub();
    event.stopImmediatePropagation = sinon.stub();
    return event;
  }

  it('shows a confirm dialog using the text from the data-confirm-message attribute', () => {
    const {ctrl, fakeWindow, confirmMessage} = component(true);

    ctrl.element.dispatchEvent(new Event('click'));

    assert.calledOnce(fakeWindow.confirm);
    assert.calledWithExactly(fakeWindow.confirm, confirmMessage);
  });

  it('prevents form submission if the user refuses the confirm dialog', () => {
    const ctrl = component(false).ctrl;
    const event = fakeEvent();

    ctrl.element.dispatchEvent(event);

    assert.called(event.preventDefault);
    assert.called(event.stopPropagation);
    assert.called(event.stopImmediatePropagation);
  });

  it('allows form submission if the user confirms the confirm dialog', () => {
    const ctrl = component(true).ctrl;
    const event = fakeEvent();

    ctrl.element.dispatchEvent(event);

    assert.isFalse(event.preventDefault.called);
    assert.isFalse(event.stopPropagation.called);
    assert.isFalse(event.stopImmediatePropagation.called);
  });
});
