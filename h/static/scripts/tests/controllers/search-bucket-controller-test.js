'use strict';

var SearchBucketController = require('../../controllers/search-bucket-controller');
var util = require('./util');

var TEMPLATE = [
  '<div class="js-search-bucket">',
  '<div class="js-header"></div>',
  '<div class="js-content"></div>',
  '</div>',
];

describe('SearchBucketController', function () {
  var container;
  var headerEl;
  var contentEl;
  var ctrl;

  beforeEach(function () {
    container = util.setupComponent(document, TEMPLATE, {
      '.js-search-bucket': SearchBucketController,
    });
    headerEl = container.querySelector('.js-header');
    contentEl = container.querySelector('.js-content');
    ctrl = container.querySelector('.js-search-bucket').controllers[0];
  });

  it('toggles content expanded state when clicked', function () {
    headerEl.dispatchEvent(new Event('click'));
    assert.isTrue(contentEl.classList.contains('is-expanded'));
  });

  it('scrolls element into view when expanded', function () {
    ctrl.scrollTo = sinon.stub();
    headerEl.dispatchEvent(new Event('click'));
    assert.calledWith(ctrl.scrollTo, container.querySelector('.js-search-bucket'));
  });
});
