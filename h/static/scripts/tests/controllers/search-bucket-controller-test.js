'use strict';

var SearchBucketController = require('../../controllers/search-bucket-controller');
var util = require('./util');

var TEMPLATE = [
  '<div class="js-search-bucket">',
  '<div data-ref="header"></div>',
  '<div data-ref="content"></div>',
  '</div>',
].join('\n');

class FakeEnvFlags {
  constructor (flags = []) {
    this.flags = flags;
  }

  get(flag) {
    return this.flags.indexOf(flag) !== -1;
  }
}

describe('SearchBucketController', function () {
  var ctrl;

  beforeEach(function () {
    ctrl = util.setupComponent(document, TEMPLATE, SearchBucketController, {
      envFlags: new FakeEnvFlags(),
    });
  });

  afterEach(function () {
    ctrl.element.remove();
  });

  it('toggles content hidden state when clicked', function () {
    ctrl.refs.header.dispatchEvent(new Event('click'));
    assert.isFalse(ctrl.refs.content.classList.contains('is-hidden'));
  });

  it('scrolls element into view when expanded', function () {
    ctrl.scrollTo = sinon.stub();
    ctrl.refs.header.dispatchEvent(new Event('click'));
    assert.calledWith(ctrl.scrollTo, ctrl.element);
  });

  it('collapses search results on initial load', function () {
    assert.isFalse(ctrl.state.expanded);
  });

  context('when initial load times out', function () {
    var scrollTo;

    beforeEach(function () {
      scrollTo = sinon.stub();
      ctrl = util.setupComponent(document, TEMPLATE, SearchBucketController, {
        scrollTo: scrollTo,
        envFlags: new FakeEnvFlags(['js-timeout']),
      });
    });

    it('does not scroll page on initial load', function () {
      assert.notCalled(scrollTo);
    });

    it('expands bucket on initial load', function () {
      assert.isTrue(ctrl.state.expanded);
    });
  });
});
