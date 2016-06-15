'use strict';

var angular = require('angular');

/**
 * Fetch all annotations in the same thread as `id`.
 *
 * @return Promise<Array<Annotation>>
 */
function fetchThread(store, id) {
  var annot;
  return store.AnnotationResource.get({id: id}).$promise.then(function (annot) {
    if (annot.references && annot.references.length) {
      // This is a reply, fetch the top-level annotation
      return store.AnnotationResource.get({id: annot.references[0]}).$promise;
    } else {
      return annot;
    }
  }).then(function (annot_) {
    annot = annot_;
    return store.SearchResource.get({references: annot.id}).$promise;
  }).then(function (searchResult) {
    return [annot].concat(searchResult.rows);
  });
}

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

  function thread() {
    return rootThread.thread(annotationUI.getState());
  }

  annotationUI.subscribe(function () {
    $scope.virtualThreadList = {
      visibleThreads: thread().children,
      offscreenUpperHeight: '0px',
      offscreenLowerHeight: '0px',
    };
  });

  $scope.setCollapsed = function (id, collapsed) {
    annotationUI.setCollapsed(id, collapsed);
  };

  this.ready = fetchThread(store, id).then(function (annots) {
    annotationMapper.loadAnnotations(annots);

    var topLevelID = annots.filter(function (annot) {
      return (annot.references || []).length === 0;
    })[0];

    if (!topLevelID) {
      return;
    }

    streamFilter
      .setMatchPolicyIncludeAny()
      .addClause('/references', 'one_of', topLevelID, true)
      .addClause('/id', 'equals', topLevelID, true);
    streamer.setConfig('filter', { filter: streamFilter.getFilter() });

    annots.forEach(function (annot) {
      annotationUI.setCollapsed(annot.id, false);
    });
  });
}

module.exports = AnnotationViewerController;
