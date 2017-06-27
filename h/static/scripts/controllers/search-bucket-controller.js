'use strict';

const scrollIntoView = require('scroll-into-view');

const Controller = require('../base/controller');
const setElementState = require('../util/dom').setElementState;

/**
 * @typedef Options
 * @property {EnvironmentFlags} [envFlags] - Environment flags. Provided as a
 *           test seam.
 * @property {Function} [scrollTo] - A function that scrolls a given element
 *           into view. Provided as a test seam.
 */

/**
 * Controller for buckets of results in the search result list
 */
class SearchBucketController extends Controller {
  /**
   * @param {Element} element
   * @param {Options} options
   */
  constructor(element, options) {
    super(element, options);

    this.scrollTo = this.options.scrollTo || scrollIntoView;

    this.refs.header.addEventListener('click', (event) => {
      if (this.refs.domainLink.contains(event.target)) {
        return;
      }

      event.stopPropagation();
      event.preventDefault();

      this.setState({expanded: !this.state.expanded});
    });

    this.refs.title.addEventListener('click', (event) => {
      event.stopPropagation();
      event.preventDefault();

      this.setState({expanded: !this.state.expanded});
    });

    this.refs.collapseView.addEventListener('click', () => {
      this.setState({expanded: !this.state.expanded});
    });

    const envFlags = this.options.envFlags || window.envFlags;

    this.setState({
      expanded: !!envFlags.get('js-timeout'),
    });
  }

  update(state, prevState) {
    setElementState(this.refs.content, {expanded: state.expanded});
    setElementState(this.element, {expanded: state.expanded});

    this.refs.title.setAttribute('aria-expanded', state.expanded.toString());

    // Scroll to element when expanded, except on initial load
    if (typeof prevState.expanded !== 'undefined' && state.expanded) {
      this.scrollTo(this.element);
    }
  }
}

module.exports = SearchBucketController;
