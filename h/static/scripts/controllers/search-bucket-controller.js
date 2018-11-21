'use strict';

const scrollIntoView = require('scroll-into-view');

const Controller = require('../base/controller');
const setElementState = require('../util/dom').setElementState;

function delay(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

/**
 * @typedef Options
 * @property {EnvironmentFlags} [envFlags] - Environment flags. Provided as a
 *           test seam.
 * @property {Function} [scrollTo] - A function that scrolls a given element
 *           into view. Provided as a test seam.
 * @property {Function} [fetch] - Fetch API. Test seam.
 * @property {Function} [delay] - Test seam.
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

    this.options.fetch = this.options.fetch || window.fetch;
    this.options.delay = this.options.delay || delay;

    /**
     * Promise which resolves when the content for this bucket has been fetched,
     * or `null` if fetching has not been triggered.
     */
    this.fetched = null;

    if (!this.refs.annotationCards) {
      // Lazy rendering is disabled and this bucket has already been populated.
      this.fetched = Promise.resolve();
    }

    this.scrollTo = this.options.scrollTo || scrollIntoView;

    this.refs.header.addEventListener('click', (event) => {
      if (this.refs.domainLink.contains(event.target)) {
        return;
      }

      event.stopPropagation();
      event.preventDefault();

      this.toggle();
    });

    this.refs.title.addEventListener('click', (event) => {
      event.stopPropagation();
      event.preventDefault();

      this.toggle();
    });

    this.refs.collapseView.addEventListener('click', () => {
      this.toggle();
    });

    const envFlags = this.options.envFlags || window.envFlags;

    this.setState({
      expanded: !!envFlags.get('js-timeout'),
    });

    // Trigger a pre-emptive fetch when the user begins to click/tap a bucket.
    // This makes the bucket content appear to load faster.
    this.element.addEventListener('mousedown', () => {
      this.fetchContent();
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

    // Fetch content on initial expand.
    if (state.expanded && this.fetched === null) {
      this.fetchContent();
    }
  }

  /**
   * Toggle the expanded state of the bucket, fetching content beforehand if
   * necessary.
   */
  toggle() {
    if (this.state.expanded) {
      this.setState({ expanded: false });
      return Promise.resolve();
    }

    // Fetch the bucket content and then expand it. If the fetch is quick
    // then delay showing the bucket until it is ready to avoid a flash of
    // missing content. Otherwise the bucket will be expanded with a loading
    // indicator visible.
    const delay = this.options.delay;
    return Promise.race([delay(300), this.fetchContent()]).then(() => {
      this.setState({ expanded: true });
    });
  }

  /**
   * Fetch and populate the HTML content of the bucket.
   */
  fetchContent() {
    if (this.fetched) {
      return this.fetched;
    }

    const container = this.refs.annotationCards;
    const annotationIds = container.dataset.ids.split(',');
    const fetchOpts = {
      method: 'POST',
      body: JSON.stringify({ annotation_ids: annotationIds }),
    };
    const fetch = this.options.fetch;

    // Display a loading indicator. If the user has a reasonably fast connection,
    // they should not usually see this.
    //
    // TODO - Make the loading indicator look prettier in case the user does
    // see it.
    container.innerHTML = '...';

    this.fetched = fetch('/search/bucket', fetchOpts).then((rsp) => {
      return rsp.text();
    }).then((html) => {
      container.innerHTML = html;
    }).catch((err) => {
      container.textContent = `Unable to fetch annotations: ${err.message}`;

      // Try again the next time the bucket is expanded.
      this.fetched = null;
    });

    return this.fetched;
  }
}

module.exports = SearchBucketController;
