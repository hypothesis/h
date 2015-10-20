'use strict';

var util = require('./util');

describe('sortDropdown', function () {
  before(function () {
    angular.module('app', [])
      .directive('sortDropdown', require('../sort-dropdown'));
  });

  beforeEach(function () {
    angular.mock.module('app');
    angular.mock.module('h.templates');
  });

  it('should update the sort mode on click', function () {
    var changeSpy = sinon.spy();
    var elem = util.createDirective(document, 'sortDropdown', {
      sortOptions: ['Newest', 'Oldest'],
      sortBy: 'Newest',
      onChangeSortBy: {
        args: ['sortBy'],
        callback: changeSpy,
      }
    });
    var links = elem.find('li');
    angular.element(links[0]).click();
    assert.calledWith(changeSpy, 'Newest');
  });
});
