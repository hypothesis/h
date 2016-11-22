'use strict';

const escapeHtml = require('escape-html');

const Controller = require('../base/controller');
const searchTextParser = require('../util/search-text-parser');

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
    const lozTempContainer = document.createElement('div');
    let lozengeEl = document.createElement('div');
    let lozengeMarkup = escapeHtml(options.content);
    const currentLozenges = containerEl.querySelectorAll('.lozenge');

    if (searchTextParser.hasKnownNamedQueryTerm(options.content)) {
      const queryTerm = searchTextParser.getLozengeFacetNameAndValue(options.content);
      lozengeMarkup = '<span class="lozenge__facet-name">' +
        escapeHtml(queryTerm.facetName) +
        '</span>' +
        ':' +
        '<span class="lozenge__facet-value">' +
        escapeHtml(queryTerm.facetValue) +
        '</span>';
    }
    lozengeEl.innerHTML =
      '<div class="js-lozenge__content lozenge__content">'+
      lozengeMarkup +
      '</div>' +
      '<div class="js-lozenge__close lozenge__close">' +
      '<img alt="Delete lozenge" src="/assets/images/icons/lozenge-close.svg">' +
      '</div>';
    lozengeEl.classList.add('lozenge');
    lozengeEl.classList.add('js-lozenge');

    lozTempContainer.appendChild(lozengeEl);

    // append the lozenge after the last lozenge child
    // or as the very first element in the container.
    // We are doing this over appendChild because we don't want to limit
    // the ability for the container to also hold other elements like an
    // input field - allowing them to flow together in the same box model
    if (currentLozenges && currentLozenges.length > 0) {
      currentLozenges[currentLozenges.length - 1].insertAdjacentHTML('afterend', lozTempContainer.innerHTML);
    } else {
      containerEl.insertAdjacentHTML('afterbegin', lozTempContainer.innerHTML);
    }

    // update reference to point to the actual dom element
    lozengeEl = containerEl.querySelectorAll('.lozenge')[currentLozenges ? currentLozenges.length : 0];

    lozengeEl.querySelector('.js-lozenge__close').addEventListener('mousedown', () => {
      lozengeEl.remove();
      options.deleteCallback();
    });
  }
}

module.exports = LozengeController;
