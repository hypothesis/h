'use strict';

var angular = require('angular');

// @ngInject
function AnnotationViewerController (
  $location, $routeParams, $scope,
  annotationUI, rootThread, streamer, store, streamFilter, annotationMapper
) {
  var id = $routeParams.id;

  // Provide no-ops until these methods are moved elsewere. They only apply
  // to annotations loaded into the stream.
  $scope.focus = angular.noop;

  $scope.search.update = function (query) {
    $location.path('/stream').search('q', query);
  };

  rootThread.on('changed', function (thread) {
    $scope.virtualThreadList = {
      visibleThreads: thread.children,
      offscreenUpperHeight: '0px',
      offscreenLowerHeight: '0px',
    };
  });

  $scope.rootThread = function () {
    return rootThread.thread();
  };

  $scope.setCollapsed = function (id, collapsed) {
    annotationUI.setCollapsed(id, collapsed);
  };

  store.AnnotationResource.get({ id: id }, function (annotation) {
    annotationMapper.loadAnnotations([annotation]);
  });

  store.SearchResource.get({ references: id }, function (data) {
    annotationMapper.loadAnnotations(data.rows);
  });

  streamFilter
    .setMatchPolicyIncludeAny()
    .addClause('/references', 'one_of', id, true)
    .addClause('/id', 'equals', id, true);

  streamer.setConfig('filter', { filter: streamFilter.getFilter() });
}

module.exports = AnnotationViewerController;
