'use strict';

var inherits = require('inherits');
var preact = require('preact');

var Controller = require('../base/controller');

var h = preact.h;

function Tooltip(props) {
  var tooltipStyle = {
    visibility: props.active ? '' : 'hidden',
    bottom: 'calc(100% + 5px)',
  };
  return h('div', {class: 'tooltip', style: tooltipStyle},
    h('span', {class: 'tooltip-label'}, props.label)
  );
}

/**
 * A custom tooltip similar to the one used in Google Docs which appears
 * instantly when activated on a target element.
 *
 * The tooltip appears when the container element is hovered with a mouse or
 * tapped.
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
    self.setState({active: true});
  });

  el.addEventListener('mouseout', function () {
    self.setState({active: false});
  });

  this.update({active: false});
}
inherits(TooltipController, Controller);

TooltipController.prototype.update = function (state) {
  var label = this.element.getAttribute('aria-label');

  preact.render(h(Tooltip, {active: state.active, label: label}),
    this.element, this.element.lastChild);
};

module.exports = TooltipController;
