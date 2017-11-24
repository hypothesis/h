'use strict';

const FormCancelController = require('../../controllers/form-cancel-controller');

describe('FormCancelController', () => {
  it('should close the window when clicked', () => {
    const fakeWindow = { close: sinon.stub() };
    const btn = document.createElement('button');
    new FormCancelController(btn, { window: fakeWindow });

    btn.click();

    assert.called(fakeWindow.close);
  });
});
