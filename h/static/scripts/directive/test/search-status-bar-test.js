'use strict';

var util = require('./util');

describe('searchStatusBar', function () {
  before(function () {
    angular.module('app', [])
      .directive('searchStatusBar', require('../search-status-bar'));
  });

  beforeEach(function () {
    angular.mock.module('app');
    angular.mock.module('h.templates');
  });

  it('should display the filter count', function () {
    var elem = util.createDirective(document, 'searchStatusBar', {
      newDesign: true,
      filterActive: true,
      filterMatchCount: 5
    });
    assert.include($(elem).text(), "5 search results");
  });

  it('should display the selection count', function () {
    var elem = util.createDirective(document, 'searchStatusBar', {
      newDesign: true,
      selectionCount: 2
    });
    assert.include($(elem).text(), '2 selected annotations');
  });
});
