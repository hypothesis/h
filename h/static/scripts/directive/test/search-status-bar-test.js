'use strict';

var angular = require('angular');

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

  context('when there is a filter', function () {
    it('should display the filter count', function () {
      var elem = util.createDirective(document, 'searchStatusBar', {
        filterActive: true,
        filterMatchCount: 5
      });
      assert.include(elem[0].textContent, "5 search results");
    });
  });

  context('when there is a selection', function () {
    var cases = [
      {count: 0, message: 'Show all annotations'},
      {count: 1, message: 'Show all annotations'},
      {count: 10, message: 'Show all 10 annotations'},
    ];

    cases.forEach(function (testCase) {
      it('should display the "Show all annotations" message', function () {
        var elem = util.createDirective(document, 'searchStatusBar', {
          selectionCount: 1,
          totalCount: testCase.count
        });
        var clearBtn = elem[0].querySelector('button');
        assert.include(clearBtn.textContent, testCase.message);
      });
    });
  });
});
