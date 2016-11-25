'use strict';

const Controller = require('../base/controller');
const searchTextParser = require('../util/search-text-parser');
const { setElementState } = require('../util/dom');

/**
 * A lozenge representing a single search term.
 *
 * A lozenge consists of two parts - the lozenge content and the 'x' button
 * which when clicked calls the `deleteCallback` handler passed in the
 * controller's options.
 *
 * const lozenge = new Lozenge(element, {
 *   content,
 *   deleteCallback,
 * });
 */
class LozengeController extends Controller {

  constructor(element, options) {
    super(element, options);

    // Work-around for HTMLFormElement#submit() failing in Firefox if a submit
    // button removes itself during click event handler.
    //
    // See https://bugzilla.mozilla.org/show_bug.cgi?id=494755#c4 and
    // https://bugzilla.mozilla.org/show_bug.cgi?id=586329
    this.refs.deleteButton.type = 'button';

    let facetName = '';
    let facetValue = options.content;

    if (searchTextParser.hasKnownNamedQueryTerm(options.content)) {
      const queryTerm = searchTextParser.getLozengeFacetNameAndValue(options.content);
      facetName = queryTerm.facetName;
      facetValue = queryTerm.facetValue;
    }

    element.classList.add('js-lozenge');

    this.refs.deleteButton.addEventListener('click', (event) => {
      event.preventDefault();
      options.deleteCallback();
    });

    this.setState({
      facetName,
      facetValue,
      disabled: false,
    });
  }

  update(state) {
    setElementState(this.element, {disabled: state.disabled});
    let facetName = state.facetName;
    if (facetName) {
      facetName += ':';
    }
    this.refs.facetName.textContent = facetName;
    this.refs.facetValue.textContent = state.facetValue;
  }

  inputValue() {
    if (this.state.facetName) {
      return this.state.facetName + ':' + this.state.facetValue;
    } else {
      return this.state.facetValue;
    }
  }
}

module.exports = LozengeController;
