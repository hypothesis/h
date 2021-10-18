import { TooltipController } from '../../controllers/tooltip-controller';

describe('TooltipController', () => {
  let targetEl;
  let template;
  let testEl;
  let tooltipEl;

  before(() => {
    template =
      '<div class="form-input__hint-icon js-tooltip"' +
      'aria-label="Test"></div>';
  });

  beforeEach(() => {
    testEl = document.createElement('div');
    testEl.innerHTML = template;

    targetEl = testEl.querySelector('div');
    new TooltipController(targetEl);

    tooltipEl = testEl.querySelector('.tooltip');
  });

  it('appears when the target is hovered', () => {
    targetEl.dispatchEvent(new Event('mouseover'));
    assert.equal(tooltipEl.style.visibility, '');
  });

  it('sets the label from the target\'s "aria-label" attribute', () => {
    targetEl.dispatchEvent(new Event('mouseover'));
    assert.equal(tooltipEl.textContent, 'Test');
  });

  it('disappears when the target is unhovered', () => {
    targetEl.dispatchEvent(new Event('mouseout'));
    assert.equal(tooltipEl.style.visibility, 'hidden');
  });
});
