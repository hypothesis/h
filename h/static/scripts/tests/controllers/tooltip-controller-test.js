'use strict';

var TooltipController = require('../../controllers/tooltip-controller');

describe('TooltipController', function () {
  var targetEl;
  var template;
  var testEl;
  var tooltipEl;

  before(function () {
    template = '<div class="form-input__hint-icon js-tooltip"' +
     'aria-label="Test"></div>';
  });

  beforeEach(function () {
    testEl = document.createElement('div');
    testEl.innerHTML = template;

    targetEl = testEl.querySelector('div');
    new TooltipController(targetEl);

    tooltipEl = testEl.querySelector('.tooltip');
  });


  it('appears when the target is hovered', function () {
    targetEl.dispatchEvent(new Event('mouseover'));
    assert.equal(tooltipEl.style.visibility, '');
  });

  it('sets the label from the target\'s "aria-label" attribute', function () {
    targetEl.dispatchEvent(new Event('mouseover'));
    assert.equal(tooltipEl.textContent, 'Test');
  });

  it('disappears when the target is unhovered', function () {
    targetEl.dispatchEvent(new Event('mouseout'));
    assert.equal(tooltipEl.style.visibility, 'hidden');
  });
});
