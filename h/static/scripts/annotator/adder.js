'use strict';

var classnames = require('classnames');

/**
 * Show the adder above the selection with an arrow pointing down at the
 * selected text.
 */
var ARROW_POINTING_DOWN = 1;

/**
 * Returns the HTML template for the adder.
 */
function template() {
  return require('./adder.html');
}

/**
 * Controller for the 'adder' toolbar which appears next to the selection
 * and provides controls for the user to create new annotations.
 *
 * @param {JQuery} element - jQuery element for the adder.
 */
function Adder(element) {
  this.hide = function () {
    element.hide();
  };

  this.showAt = function (position, arrowDirection) {
    element[0].className = classnames({
      'annotator-adder': true,
      'annotator-adder--arrow-down': arrowDirection === ARROW_POINTING_DOWN,
    });
    element[0].style.top = position.top;
    element[0].style.left = position.left;
    element.show();
  };
}

module.exports = {
  ARROW_POINTING_DOWN: ARROW_POINTING_DOWN,
  template: template,
  Adder: Adder,
};
