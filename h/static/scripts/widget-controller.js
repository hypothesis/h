'use strict';

var angular = require('angular');

var events = require('./events');

// @ngInject
module.exports = function WidgetController(
  $scope, $rootScope, annotationUI, crossframe, annotationMapper,
  drafts, groups, streamer, streamFilter, store, threading
) {
  $scope.threadRoot = threading.root;
  $scope.sortOptions = ['Newest', 'Oldest', 'Location'];

  var DEFAULT_CHUNK_SIZE = 200;
  var loaded = [];

  var _resetAnnotations = function () {
    // Unload all the annotations
    annotationMapper.unloadAnnotations(threading.annotationList());
    // Reload all the drafts
    threading.thread(drafts.unsaved());
  };

  var _loadAnnotationsFrom = function (query, offset) {
    var queryCore = {
      limit: $scope.chunkSize || DEFAULT_CHUNK_SIZE,
      offset: offset,
      sort: 'created',
      order: 'asc',
      group: groups.focused().id
    };
    var q = angular.extend(queryCore, query);
    q._separate_replies = true;

    store.SearchResource.get(q, function (results) {
      var total = results.total;
      offset += results.rows.length;
      if (offset < total) {
        _loadAnnotationsFrom(query, offset);
      }

      annotationMapper.loadAnnotations(results.rows, results.replies);
    });
  };

  var loadAnnotations = function (frames) {
    for (var i = 0, f; i < frames.length; i++) {
      f = frames[i];
      var ref;
      if (ref = f.uri, loaded.indexOf(ref) >= 0) {
        continue;
      }
      loaded.push(f.uri);
      _loadAnnotationsFrom({uri: f.uri}, 0);
    }

    if (loaded.length > 0) {
      streamFilter.resetFilter().addClause('/uri', 'one_of', loaded);
      streamer.setConfig('filter', {filter: streamFilter.getFilter()});
    }
  };

  $scope.$on(events.GROUP_FOCUSED, function () {
    _resetAnnotations(annotationMapper, drafts, threading);
    loaded = [];
    return loadAnnotations(crossframe.frames);
  });

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
