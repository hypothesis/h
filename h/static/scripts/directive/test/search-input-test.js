'use strict';

var angular = require('angular');

var util = require('./util');

describe('searchInput', function () {
  var fakeHttp;

  before(function () {
    angular.module('app', [])
      .directive('searchInput', require('../search-input'));
  });

  beforeEach(function () {
    fakeHttp = {pendingRequests: []};
    angular.mock.module('app', {
      $http: fakeHttp,
    });
  });

  it('displays the search query', function () {
    var el = util.createDirective(document, 'searchInput', {
      query: 'foo',
    });
    var input = el.find('input')[0];
    assert.equal(input.value, 'foo');
  });

  it('invokes #onSearch() when the query changes', function () {
    var onSearch = sinon.stub();
    var el = util.createDirective(document, 'searchInput', {
      query: 'foo',
      onSearch: {
        args: ['$query'],
        callback: onSearch,
      },
    });
    var input = el.find('input')[0];
    var form = el.find('form');
    input.value = 'new-query';
    form.submit();
    assert.calledWith(onSearch, 'new-query');
  });

  describe('loading indicator', function () {
    it('is hidden when there are no network requests in flight', function () {
      var el = util.createDirective(document, 'search-input', {});
      var spinner = el[0].querySelector('.spinner');
      assert.equal(util.isHidden(spinner), true);
    });

    it('is visible when there are network requests in flight', function () {
      var el = util.createDirective(document, 'search-input', {});
      var spinner = el[0].querySelector('.spinner');
      fakeHttp.pendingRequests.push([{}]);
      el.scope.$digest();
      assert.equal(util.isHidden(spinner), false);
    });
  });
});
