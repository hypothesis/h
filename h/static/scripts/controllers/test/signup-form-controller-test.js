import { DisableOnSubmitController } from '../../controllers/disable-on-submit-controller';

const TEMPLATE = `
  <form class="js-any-form js-disable-on-submit">
    <input type="submit" class="any-submit">
  </form>
  `;

describe('DisableOnSubmitController', () => {
  let element;
  let form;
  let submitBtn;

  beforeEach(() => {
    element = document.createElement('div');
    element.innerHTML = TEMPLATE;
    form = element.querySelector('.js-disable-on-submit');
    submitBtn = element.querySelector('.any-submit');
  });

  it('disables the submit button on form submit', () => {
    new DisableOnSubmitController(form);
    assert.isFalse(submitBtn.disabled);
    form.dispatchEvent(new Event('submit'));
    assert.isTrue(submitBtn.disabled);
  });
});
