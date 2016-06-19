'use strict';

var angular = require('angular');

var util = require('./util');

describe('selectionTabs', function () {
  before(function () {
    angular.module('app', [])
      .directive('selectionTabs', require('../selection-tabs'));
  });

  beforeEach(function () {
    var fakeAnnotationUI = {};
    angular.mock.module('app', {
      annotationUI: fakeAnnotationUI,
    });
  });

  context('displays selection tabs, counts and a selection', function () {
    it('should display the tabs and counts of annotations and notes', function () {
      var elem = util.createDirective(document, 'selectionTabs', {
        selectedTab: 'annotation',
        totalAnnotations: '123',
        totalNotes: '456',
        tabAnnotations: 'annotation',
        tabNotes: 'note',
      });

      var tabs = elem[0].querySelectorAll('li');
      var sups = elem[0].querySelectorAll('sup');

      assert.include(tabs[0].textContent, "Annotations");
      assert.include(tabs[1].textContent, "Notes");
      assert.include(sups[0].textContent, "123");
      assert.include(sups[1].textContent, "456");
    });

    it('should display annotations tab as selected', function () {
      var elem = util.createDirective(document, 'selectionTabs', {
        selectedTab: 'annotation',
        totalAnnotations: '123',
        totalNotes: '456',
        tabAnnotations: 'annotation',
        tabNotes: 'note',
      });

      var tabs = elem[0].querySelectorAll('li');

      assert.include(tabs[0].className, "selection-tabs--selected");
    });

    it('should display notes tab as selected', function () {
      var elem = util.createDirective(document, 'selectionTabs', {
        selectedTab: 'note',
        totalAnnotations: '123',
        totalNotes: '456',
        tabAnnotations: 'annotation',
        tabNotes: 'note',
      });

      var tabs = elem[0].querySelectorAll('li');

      assert.include(tabs[1].className, "selection-tabs--selected");
    });
  });
});
