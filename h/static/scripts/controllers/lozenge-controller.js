'use strict';

var Controller = require('../base/controller');

/**
 * Create a lozenge with options.content as its content and append it to containerEl.
 *
 * A lozenge is made of two parts - the lozenge content and
 * the 'x' button which when clicked removes the lozenge
 * from the container and executes the delete callback provided.
 *
 * var lozenge = new Lozenge(containerEl, {
 *   content: content,
 *   deleteCallback: deleteCallback,
 * });
 */
class LozengeController extends Controller {
  constructor(containerEl, options) {
    super(containerEl, options);
    var lozengeEl = document.createElement('div');
    lozengeEl.innerHTML =
      '<div class="js-lozenge__content lozenge__content">'+
      options.content+
      '</div>' +
      '<div class="js-lozenge__close lozenge__close">' +
      '<img alt="Delete lozenge" src="/assets/images/icons/lozenge-close.svg">' +
      '</div>';
    lozengeEl.classList.add('lozenge');
    lozengeEl.classList.add('js-lozenge');
    containerEl.appendChild(lozengeEl);

    lozengeEl.querySelector('.js-lozenge__close').addEventListener('mousedown', () => {
      lozengeEl.remove();
      options.deleteCallback();
    });
  }
}

module.exports = LozengeController;
