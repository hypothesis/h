'use strict';

var angular = require('angular');

var events = require('./events');
var SearchClient = require('./search-client');

/**
 * Returns the group ID of the first annotation in @p results whose
 * ID is a key in @p selection.
 */
function groupIDFromSelection(selection, results) {
  var id = Object.keys(selection)[0];
  var annot = results.find(function (annot) {
    return annot.id === id;
  });
  if (!annot) {
    return;
  }
  return annot.group;
}

// @ngInject
module.exports = function WidgetController(
  $scope, $rootScope, annotationUI, crossframe, annotationMapper,
  drafts, groups, streamer, streamFilter, store, threading
) {
  $scope.threadRoot = threading.root;
  $scope.sortOptions = ['Newest', 'Oldest', 'Location'];

  function _resetAnnotations() {
    // Unload all the annotations
    annotationMapper.unloadAnnotations(threading.annotationList());
    // Reload all the drafts
    threading.thread(drafts.unsaved());
  }

  var searchClients = [];

  function _loadAnnotationsFor(uri, group) {
    var searchClient = new SearchClient(store.SearchResource, {
      // If no group is specified, we are fetching annotations from
      // all groups in order to find out which group contains the selected
      // annotation, therefore we need to load all chunks before processing
      // the results
      incremental: !!group,
    });
    searchClients.push(searchClient);
    searchClient.on('results', function (results) {
      if (annotationUI.hasSelectedAnnotations()) {
        var groupID = groupIDFromSelection(annotationUI.selectedAnnotationMap,
          results);
        if (!groupID) {
          // If the selected annotation is not available, fall back to
          // loading annotations for the currently focused group
          groupID = groups.focused().id;
        }
        groups.focus(groupID);
        results = results.filter(function (result) {
          return result.group === groupID;
        });
      }
      if (results.length) {
        annotationMapper.loadAnnotations(results);
      }
    });
    searchClient.on('end', function () {
      searchClients.splice(searchClients.indexOf(searchClient), 1);
    });
    searchClient.get({uri: uri, group: group});
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

    // If there is no selection, load annotations only for the focused group.
    //
    // If there is a selection, we load annotations for all groups, find out
    // which group the first selected annotation is in and then filter the
    // results on the client by that group.
    //
    // In the common case where the total number of annotations on
    // a page that are visible to the user is not greater than
    // the batch size, this saves an extra roundtrip to the server
    // to fetch the selected annotation in order to determine which group
    // it is in before fetching the remaining annotations.
    var group = annotationUI.hasSelectedAnnotations() ?
      null : groups.focused().id;

    for (var i=0; i < urls.length; i++) {
      _loadAnnotationsFor(urls[i], group);
    }

    if (urls.length > 0) {
      streamFilter.resetFilter().addClause('/uri', 'one_of', urls);
      streamer.setConfig('filter', {filter: streamFilter.getFilter()});
    }
  };

  $scope.$on(events.GROUP_FOCUSED, function () {
    if (searchClients.length) {
      // If the current group changes as a _result_ of loading annotations,
      // avoid trying to load annotations again.
      //
      // If however the group changes because of a user action during
      // loading of annotations, we should cancel the current load.
      return;
    }

    annotationUI.clearSelectedAnnotations();
    _resetAnnotations();
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
