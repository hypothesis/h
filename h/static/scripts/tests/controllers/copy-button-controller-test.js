import { CopyButtonController } from '../../controllers/copy-button-controller';

import { setupComponent } from './util';

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
    sinon.stub(document, 'execCommand').callsFake(command => {
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

  it('makes the input field read-only', () => {
    assert.isTrue(ctrl.refs.input.readOnly);
  });

  it('leaves the input field read-write on Mobile Safari', () => {
    const mobileSafariUserAgent =
      'Mozilla/5.0 (iPhone; CPU iPhone OS 10_0 like Mac OS X) AppleWebKit/602.1.38 (KHTML, like Gecko) Version/10.0 Mobile/14A5297c Safari/602.1';
    ctrl = setupComponent(document, template, CopyButtonController, {
      userAgent: mobileSafariUserAgent,
    });
    assert.isFalse(ctrl.refs.input.readOnly);
  });
});
