'use strict';

var SearchBucketController = require('../../controllers/search-bucket-controller');
var util = require('./util');

var TEMPLATE = [
  '<div class="js-search-bucket">',
  '<div data-ref="header"></div>',
  '<div data-ref="content"></div>',
  '</div>',
].join('\n');

describe('SearchBucketController', function () {
  var ctrl;

  beforeEach(function () {
    ctrl = util.setupComponent(document, TEMPLATE, SearchBucketController);
  });

  afterEach(function () {
    ctrl.element.remove();
  });

  it('toggles content expanded state when clicked', function () {
    ctrl.refs.header.dispatchEvent(new Event('click'));
    assert.isTrue(ctrl.refs.content.classList.contains('is-expanded'));
  });

  it('scrolls element into view when expanded', function () {
    ctrl.scrollTo = sinon.stub();
    ctrl.refs.header.dispatchEvent(new Event('click'));
    assert.calledWith(ctrl.scrollTo, ctrl.element);
  });
});
