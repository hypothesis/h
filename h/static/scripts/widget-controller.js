'use strict';

var angular = require('angular');

var events = require('./events');
var SearchClient = require('./search-client');

// @ngInject
module.exports = function WidgetController(
  $scope, $rootScope, annotationUI, crossframe, annotationMapper,
  drafts, groups, streamer, streamFilter, store, threading
) {
  $scope.threadRoot = threading.root;
  $scope.sortOptions = ['Newest', 'Oldest', 'Location'];

  var _resetAnnotations = function () {
    // Unload all the annotations
    annotationMapper.unloadAnnotations(threading.annotationList());
    // Reload all the drafts
    threading.thread(drafts.unsaved());
  };

  var searchClients = [];

  function _loadAnnotationsFor(uri, group) {
    var searchClient = new SearchClient(store.SearchResource);
    searchClients.push(searchClient);
    searchClient.on('results', function (results) {
      annotationMapper.loadAnnotations(results);
    });
    searchClient.on('end', function () {
      searchClients.splice(searchClients.indexOf(searchClient), 1);
    });
    searchClient.get({
      uri: uri,
      group: group,
    });
  }

  /**
   * Load annotations for all URLs associated with @p frames.
   *
   * @param {Array<{uri:string}>} frames - Hypothesis client frames
   *        to load annotations for.
   */
  var loadAnnotations = function (frames) {
    searchClients.forEach(function (client) {
      client.cancel();
    });

    var urls = frames.reduce(function (urls, frame) {
      if (urls.indexOf(frame.uri) !== -1) {
        return urls;
      } else {
        return urls.concat(frame.uri);
      }
    }, []);

    for (var i=0; i < urls.length; i++) {
      _loadAnnotationsFor(urls[i], groups.focused().id);
    }

    if (urls.length > 0) {
      streamFilter.resetFilter().addClause('/uri', 'one_of', urls);
      streamer.setConfig('filter', {filter: streamFilter.getFilter()});
    }
  };

  $scope.$on(events.GROUP_FOCUSED, function () {
    annotationUI.clearSelectedAnnotations();
    _resetAnnotations(annotationMapper, drafts, threading);
    return loadAnnotations(crossframe.frames);
  });

  // Watch anything that may require us to reload annotations.
  $scope.$watchCollection(function () {
    return crossframe.frames;
  }, loadAnnotations);

  $scope.focus = function (annotation) {
    var highlights = [];
    if (angular.isObject(annotation)) {
      highlights = [annotation.$$tag];
    }
    return crossframe.call('focusAnnotations', highlights);
  };

  $scope.scrollTo = function (annotation) {
    if (angular.isObject(annotation)) {
      return crossframe.call('scrollToAnnotation', annotation.$$tag);
    }
  };

  $scope.hasFocus = function (annotation) {
    if (!annotation || !$scope.focusedAnnotations) {
      return false;
    }
    return annotation.$$tag in $scope.focusedAnnotations;
  };

  $rootScope.$on('beforeAnnotationCreated', function (event, data) {
    if (data.$highlight || (data.references && data.references.length > 0)) {
      return;
    }
    return $scope.clearSelection();
  });
};
