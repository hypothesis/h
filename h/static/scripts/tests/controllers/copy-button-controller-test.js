'use strict';

const CopyButtonController = require('../../controllers/copy-button-controller');
const { setupComponent } = require('./util');

describe('CopyButtonController', () => {
  const template = `<div>
    <input data-ref="input">
    <button data-ref="button"></button>
  </div>`;

  let copiedText;
  let copySuccess;
  let ctrl;

  beforeEach(() => {
    copySuccess = false;
    copiedText = '';
    sinon.stub(document, 'execCommand', (command) => {
      if (command === 'copy') {
        copiedText = document.getSelection().toString();
        return copySuccess;
      }
      return false;
    });
    ctrl = setupComponent(document, template, CopyButtonController);
    ctrl.refs.input.value = 'Text to copy';
  });

  afterEach(() => {
    document.execCommand.restore();
  });

  it('copies text when button is clicked', () => {
    copySuccess = true;
    ctrl.refs.button.click();
    assert.equal(copiedText, 'Text to copy');
  });

  it('displays success message if text was copied', () => {
    copySuccess = true;
    ctrl.refs.button.click();
    assert.include(ctrl.refs.input.value, 'Link copied');
  });

  it('displays alternative message if text was not copied', () => {
    copySuccess = false;
    ctrl.refs.button.click();
    assert.include(ctrl.refs.input.value, 'Copying link failed');
  });
});
