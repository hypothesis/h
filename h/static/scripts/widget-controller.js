'use strict';

var events = require('./events');
var SearchClient = require('./search-client');

/**
 * Returns the group ID of the first annotation in `results` whose
 * ID matches `id`
 *
 * @param {string} id
 * @param {Array<Annotation>} results
 */
function groupIDFromAnnotation(id, results) {
  var annot = results.find(function (annot) {
    return annot.id === id;
  });
  if (!annot) {
    return;
  }
  return annot.group;
}

/**
 * Return the parent annotation of `annot` which may be either an annotation
 * or a reply.
 *
 * @param {Threading} threading - Threading service
 * @param {Annotation} annot
 */
function rootAncestorOf(threading, annot) {
  if (!annot.references ||
       annot.references.length === 0) {
    return annot;
  }

  // Replies can be nested, we're only interested in the root ancestor
  // which is an annotation rather than a reply.
  var root = threading.idTable[annot.references[0]].message;
  if (!root) {
    return annot;
  }
  return root;
}

// @ngInject
module.exports = function WidgetController(
  $scope, $rootScope, annotationUI, crossframe, annotationMapper,
  drafts, groups, settings, streamer, streamFilter, store, threading
) {
  $scope.threadRoot = threading.root;
  $scope.sortOptions = ['Newest', 'Oldest', 'Location'];

  function focusAnnotation(annotation) {
    var highlights = [];
    if (annotation) {
      highlights = [annotation.$$tag];
    }
    crossframe.call('focusAnnotations', highlights);
  }

  function scrollToAnnotation(annotation) {
    if (!annotation) {
      return;
    }
    crossframe.call('scrollToAnnotation', annotation.$$tag);
  }

  /**
   * Returns the ID of the direct-linked annotation (if any).
   * This ID is passed to the app via an 'id:<annotation ID>' search query
   */
  function directLinkedAnnotationID() {
    var idMatch = $scope.search.query.match(/^id:(.*)$/);
    if (idMatch) {
      return idMatch[1];
    } else {
      return null;
    }
  }

  /**
   * Returns the Annotation object for the first annotation in the
   * selected annotation set. Note that 'first' refers to the order
   * of annotations passed to annotationUI when selecting annotations,
   * not the order in which they appear in the document.
   */
  function directLinkedAnnotation() {
    var id = directLinkedAnnotationID();
    if (!id) {
      return null;
    }
    return threading.idTable[id] && threading.idTable[id].message;
  }

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
      // all groups in order to find out which group contains the direct-linked
      // annotation, therefore we need to load all chunks before processing
      // the results
      incremental: !!group,
    });
    searchClients.push(searchClient);
    searchClient.on('results', function (results) {
      if (directLinkedAnnotationID()) {
        // Focus the group containing the annotation and filter
        // annotations to those from this group
        var groupID = groupIDFromAnnotation(directLinkedAnnotationID(),
          results);
        if (!groupID) {
          // If the selected annotation is not available, fall back to
          // loading annotations for the currently focused group
          groupID = groups.focused().id;
        }
        results = results.filter(function (result) {
          return result.group === groupID;
        });
        groups.focus(groupID);
      }

      if (results.length) {
        annotationMapper.loadAnnotations(results);
      }
    });
    searchClient.on('end', function () {
      // Remove client from list of active search clients
      searchClients.splice(searchClients.indexOf(searchClient), 1);
    });
    searchClient.get({uri: uri, group: group});
  }

  /**
   * Load annotations for all URLs associated with `frames`.
   *
   * @param {Array<{uri:string}>} frames - Hypothesis client frames
   *        to load annotations for.
   */
  function loadAnnotations(frames) {
    _resetAnnotations();

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

    // If there is no direct-linked annotation, load annotations only for the
    // focused group, otherwise we load annotations for all groups, find out
    // which group that annotation is in and then filter the results on the
    // client by that group.
    //
    // In the common case where the total number of annotations on a page that
    // are visible to the user is not greater than the batch size, this saves an
    // extra roundtrip to the server to fetch the annotation in order to
    // determine which group it is in before fetching the remaining annotations.
    var group = directLinkedAnnotationID() ?
      null : groups.focused().id;

    for (var i=0; i < urls.length; i++) {
      _loadAnnotationsFor(urls[i], group);
    }

    if (urls.length > 0) {
      streamFilter.resetFilter().addClause('/uri', 'one_of', urls);
      streamer.setConfig('filter', {filter: streamFilter.getFilter()});
    }
  }

  // When a direct-linked annotation is successfully anchored in the page,
  // focus and scroll to it
  $rootScope.$on(events.ANNOTATIONS_SYNCED, function (event, tags) {
    var annot = directLinkedAnnotation();
    if (!annot) {
      return;
    }

    if (!tags.some(function (tag) { return tag.tag === annot.$$tag; })) {
      return;
    }

    // Only annotations (not replies) can be scrolled to and focused, so
    // we need to find the parent of the direct-linked annotation
    // and focus/scroll to that.
    var parent = rootAncestorOf(threading, annot);
    focusAnnotation(parent);
    scrollToAnnotation(parent);
  });

  $scope.$on(events.GROUP_FOCUSED, function () {
    // The focused group may be changed during loading annotations (in which
    // case, searchClients.length > 0), as a result of switching to the group
    // containing a direct-linked annotation.
    //
    // In that case, we don't want to trigger reloading annotations again.
    if (searchClients.length) {
      return;
    }

    annotationUI.clearSelectedAnnotations();
    return loadAnnotations(crossframe.frames);
  });

  // Watch anything that may require us to reload annotations.
  $scope.$watchCollection(function () {
    return crossframe.frames;
  }, loadAnnotations);

  $scope.focus = focusAnnotation;
  $scope.scrollTo = scrollToAnnotation;

  $scope.hasFocus = function (annotation) {
    if (!annotation || !$scope.focusedAnnotations) {
      return false;
    }
    return annotation.$$tag in $scope.focusedAnnotations;
  };

  $scope.annotationUnavailable = function () {
    return searchClients.length === 0 &&
           !!directLinkedAnnotationID() &&
           !threading.idTable[directLinkedAnnotationID()];
  };

  $scope.shouldShowLoggedOutMessage = function () {
    // If user is not logged out, don't show CTA.
    if ($scope.auth.status !== 'signed-out') {
      return false;
    }

    // The user is logged out and has landed on a direct linked
    // annotation, and that annotation is available to the user,
    // show the CTA
    return searchClients.length === 0 &&
           !!directLinkedAnnotationID() &&
           !!threading.idTable[directLinkedAnnotationID()];
  };

  $rootScope.$on(events.BEFORE_ANNOTATION_CREATED, function (event, data) {
    if (data.$highlight || (data.references && data.references.length > 0)) {
      return;
    }
    return $scope.clearSelection();
  });
};
