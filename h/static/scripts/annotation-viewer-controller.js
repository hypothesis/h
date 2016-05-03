'use strict';

var angular = require('angular');

// @ngInject
function AnnotationViewerController (
  $location, $routeParams, $scope,
  streamer, store, streamFilter, annotationMapper, threading
) {
  var id = $routeParams.id;

  // Provide no-ops until these methods are moved elsewere. They only apply
  // to annotations loaded into the stream.
  $scope.focus = angular.noop;

  $scope.search.update = function (query) {
    $location.path('/stream').search('q', query);
  };

  store.AnnotationResource.get({ id: id }, function (annotation) {
    annotationMapper.loadAnnotations([annotation]);
    $scope.threadRoot = { children: [threading.idTable[id]] };
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
