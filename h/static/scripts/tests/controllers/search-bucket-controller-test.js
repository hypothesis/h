'use strict';

const SearchBucketController = require('../../controllers/search-bucket-controller');
const util = require('./util');

function template({ lazyRendering }) {
  const contentMarkup = lazyRendering ?
    '<div data-ref="annotationCards"></div>' : '';

  return `<div class="js-search-bucket">
    <div data-ref="header">
      <a data-ref="domainLink">foo.com</a>
    </div>
    <div data-ref="content">
      ${contentMarkup}
    </div>
    <a data-ref="title"></a>
    <button data-ref="collapseView"></button>
  </div>
  `;
}

const templates = {
  lazyRender: template({ lazyRendering: true }),
  noLazyRender: template({ lazyRendering: false }),
};

class FakeEnvFlags {
  constructor (flags = []) {
    this.flags = flags;
  }

  get(flag) {
    return this.flags.indexOf(flag) !== -1;
  }
}

describe('SearchBucketController', () => {
  let ctrl;

  beforeEach(() => {
    ctrl = util.setupComponent(document, templates.noLazyRender, SearchBucketController, {
      envFlags: new FakeEnvFlags(),
    });
  });

  afterEach(() => {
    ctrl.element.remove();
  });

  it('does not have the is-expanded CSS class initially', () => {
    assert.isFalse(ctrl.refs.content.classList.contains('is-expanded'));
  });

  it('adds the is-expanded CSS class when clicked', () => {
    ctrl.refs.header.dispatchEvent(new Event('click'));
    assert.isTrue(ctrl.refs.content.classList.contains('is-expanded'));
  });

  it('does not expand when domain link is clicked', () => {
    ctrl.refs.domainLink.dispatchEvent(new Event('click', {bubbles: true}));
    assert.isFalse(ctrl.refs.content.classList.contains('is-expanded'));
  });

  it('removes the is-expanded CSS class when clicked again', () => {
    ctrl.refs.header.dispatchEvent(new Event('click'));
    ctrl.refs.header.dispatchEvent(new Event('click'));
    assert.isFalse(ctrl.refs.content.classList.contains('is-expanded'));
  });

  it('removes the is-expanded CSS class when collapse view is clicked', () => {
    ctrl.refs.header.dispatchEvent(new Event('click'));
    ctrl.refs.collapseView.dispatchEvent(new Event('click'));
    assert.isFalse(ctrl.refs.content.classList.contains('is-expanded'));
  });

  it('scrolls element into view when expanded', () => {
    ctrl.scrollTo = sinon.stub();
    ctrl.refs.header.dispatchEvent(new Event('click'));
    assert.calledWith(ctrl.scrollTo, ctrl.element);
  });

  it('sets ARIA expanded state when expanded or collapsed', () => {
    ctrl.refs.title.dispatchEvent(new Event('click'));
    assert.equal(ctrl.refs.title.getAttribute('aria-expanded'), 'true');

    ctrl.refs.title.dispatchEvent(new Event('click'));
    assert.equal(ctrl.refs.title.getAttribute('aria-expanded'), 'false');
  });

  it('collapses search results on initial load', () => {
    assert.isFalse(ctrl.state.expanded);
  });

  context('when initial load times out', () => {
    let scrollTo;

    beforeEach(() => {
      scrollTo = sinon.stub();
      ctrl = util.setupComponent(document, templates.noLazyRender, SearchBucketController, {
        scrollTo: scrollTo,
        envFlags: new FakeEnvFlags(['js-timeout']),
      });
    });

    it('does not scroll page on initial load', () => {
      assert.notCalled(scrollTo);
    });

    it('expands bucket on initial load', () => {
      assert.isTrue(ctrl.state.expanded);
    });
  });

  context('when lazy rendering is enabled', () => {
    beforeEach(() => {
      // TODO
    });

    it('fetches rendered annotations when bucket is expanded', () => {
      // TODO
    });

    it('expands bucket once content is fetched', () => {
      // TODO
    });

    it('expands bucket if content is not fetched after a timeout', () => {
      // TODO
    });

    it('populates bucket with fetched HTML', () => {
      // TODO
    });

    it('does not fetch rendered annotations if already fetched', () => {
      // TODO
    });

    it('renders an error message if fetch fails', () => {
      // TODO
    });

    it('pre-fetches rendered annotations on mousedown', () => {
      // TODO
    });
  });
});
