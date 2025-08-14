import scrollIntoView from 'scroll-into-view';

import { Controller } from '../base/controller';
import { setElementState } from '../util/dom';

/**
 * @typedef Options
 * @property {Function} [scrollTo] - A function that scrolls a given element
 *           into view. Provided as a test seam.
 */

/**
 * Controller for buckets of results in the search result list
 */
export class SearchBucketController extends Controller {
  /**
   * @param {Element} element
   * @param {Options} options
   */
  constructor(element, options) {
    super(element, options);

    this.scrollTo = this.options.scrollTo || scrollIntoView;

    this.refs.header.addEventListener('click', event => {
      if (this.refs.domainLink.contains(event.target)) {
        return;
      }

      event.stopPropagation();
      event.preventDefault();

      this.setState({ expanded: !this.state.expanded });
    });

    this.refs.title.addEventListener('click', event => {
      event.stopPropagation();
      event.preventDefault();

      this.setState({ expanded: !this.state.expanded });
    });

    this.refs.collapseView.addEventListener('click', () => {
      this.setState({ expanded: !this.state.expanded });
    });

    this.setState({
      expanded: false,
    });
  }

  update(state, prevState) {
    setElementState(this.refs.content, { expanded: state.expanded });
    setElementState(this.element, { expanded: state.expanded });

    this.refs.title.setAttribute('aria-expanded', state.expanded.toString());

    // Scroll to element when expanded, except on initial load
    if (typeof prevState.expanded !== 'undefined' && state.expanded) {
      this.scrollTo(this.element);
    }
  }
}
