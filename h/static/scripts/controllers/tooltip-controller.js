'use strict';

var inherits = require('inherits');

var Controller = require('../base/controller');

/**
 * A custom tooltip similar to the one used in Google Docs which appears
 * instantly when activated on a target element.
 *
 * The tooltip is displayed and hidden by setting its target element.
 *
 *  var tooltip = new Tooltip(document.body);
 *  tooltip.setState({target: aWidget}); // Show tooltip
 *  tooltip.setState({target: null}); // Hide tooltip
 *
 * The tooltip's label is derived from the target element's 'aria-label'
 * attribute.
 *
 * @param {Element} el - The container for the tooltip.
 */
function TooltipController(el) {
  Controller.call(this, el);

  var self = this;

  // With mouse input, show the tooltip on hover. On touch devices we rely on
  // the browser to synthesize 'mouseover' events to make the tooltip appear
  // when the host element is tapped and disappear when the host element loses
  // focus.
  // See http://www.codediesel.com/javascript/making-mouseover-event-work-on-an-ipad/
  el.addEventListener('mouseover', function () {
    self.setState({target: el});
  });

  el.addEventListener('mouseout', function () {
    self.setState({target: null});
  });

  this._el = el.ownerDocument.createElement('div');
  this._el.innerHTML = '<span class="tooltip-label js-tooltip-label"></span>';
  this._el.className = 'tooltip';
  el.appendChild(this._el);
  this._labelEl = this._el.querySelector('.js-tooltip-label');

  this.setState({target: null});
}
inherits(TooltipController, Controller);

TooltipController.prototype.update = function (state) {
  if (!state.target) {
    this._el.style.visibility = 'hidden';
    return;
  }

  var target = state.target;
  var label = target.getAttribute('aria-label');
  this._labelEl.textContent = label;

  Object.assign(this._el.style, {
    visibility: '',
    bottom: 'calc(100% + 5px)',
  });
};

module.exports = TooltipController;
