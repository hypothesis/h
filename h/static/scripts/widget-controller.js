'use strict';

var SearchClient = require('./search-client');
var events = require('./events');
var memoize = require('./util/memoize');
var scopeTimeout = require('./util/scope-timeout');

function firstKey(object) {
  for (var k in object) {
    if (!object.hasOwnProperty(k)) {
      continue;
    }
    return k;
  }
  return null;
}

/**
 * Returns the group ID of the first annotation in `results` whose
 * ID is a key in `selection`.
 */
function groupIDFromSelection(selection, results) {
  var id = firstKey(selection);
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
  drafts, groups, rootThread, settings, streamer, streamFilter, store,
  VirtualThreadList
) {
  function getThreadHeight(id) {
    var threadElement = document.getElementById(id);
    if (!threadElement) {
      return;
    }

    // Get the height of the element inside the border-box, excluding
    // top and bottom margins.
    var elementHeight = threadElement.getBoundingClientRect().height;

    var style = window.getComputedStyle(threadElement);

    // Get the bottom margin of the element. style.margin{Side} will return
    // values of the form 'Npx', from which we extract 'N'.
    var marginHeight = parseFloat(style.marginTop) +
                       parseFloat(style.marginBottom);

    return elementHeight + marginHeight;
  }

  var visibleThreads = new VirtualThreadList($scope, window, rootThread.thread());
  visibleThreads.on('changed', function (state) {
    $scope.virtualThreadList = {
      visibleThreads: state.visibleThreads,
      offscreenUpperHeight: state.offscreenUpperHeight + 'px',
      offscreenLowerHeight: state.offscreenLowerHeight + 'px',
    };

    scopeTimeout($scope, function () {
      state.visibleThreads.forEach(function (thread) {
        visibleThreads.setThreadHeight(thread.id, getThreadHeight(thread.id));
      });
    }, 50);
  });
  rootThread.on('changed', function (thread) {
    visibleThreads.setRootThread(thread);
  });
  $scope.$on('$destroy', function () {
    visibleThreads.detach();
  });

  $scope.sortOptions = ['Newest', 'Oldest', 'Location'];

  function annotationExists(id) {
    return annotationUI.getState().annotations.some(function (annot) {
      return annot.id === id;
    });
  }

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
   * Returns the Annotation object for the first annotation in the
   * selected annotation set. Note that 'first' refers to the order
   * of annotations passed to annotationUI when selecting annotations,
   * not the order in which they appear in the document.
   */
  function firstSelectedAnnotation() {
    if (annotationUI.getState().selectedAnnotationMap) {
      var id = Object.keys(annotationUI.getState().selectedAnnotationMap)[0];
      return annotationUI.getState().annotations.find(function (annot) {
        return annot.id === id;
      });
    } else {
      return null;
    }
  }

  var searchClients = [];

  function _resetAnnotations() {
    // Unload all the annotations
    annotationMapper.unloadAnnotations(annotationUI.getState().annotations);
    // Reload all the drafts
    annotationUI.addAnnotations(drafts.unsaved());
  }

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
        // Focus the group containing the selected annotation and filter
        // annotations to those from this group
        var groupID = groupIDFromSelection(
          annotationUI.getState().selectedAnnotationMap, results);
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

  function isLoading() {
    return searchClients.length > 0;
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
  }

  // When a direct-linked annotation is successfully anchored in the page,
  // focus and scroll to it
  $rootScope.$on(events.ANNOTATIONS_SYNCED, function (event, tags) {
    var selectedAnnot = firstSelectedAnnotation();
    if (!selectedAnnot) {
      return;
    }
    var matchesSelection = tags.some(function (tag) {
      return tag.tag === selectedAnnot.$$tag;
    });
    if (!matchesSelection) {
      return;
    }
    focusAnnotation(selectedAnnot);
    scrollToAnnotation(selectedAnnot);
  });

  $scope.$on(events.GROUP_FOCUSED, function () {
    // The focused group may be changed during loading annotations as a result
    // of switching to the group containing a direct-linked annotation.
    //
    // In that case, we don't want to trigger reloading annotations again.
    if (isLoading()) {
      return;
    }

    annotationUI.clearSelectedAnnotations();
    return loadAnnotations(crossframe.frames);
  });

  // Watch anything that may require us to reload annotations.
  $scope.$watchCollection(function () {
    return crossframe.frames;
  }, loadAnnotations);

  // Watch the inputs that determine which annotations are currently
  // visible and how they are sorted and rebuild the thread when they change
  $scope.$watch('sort.name', function (mode) {
    annotationUI.sortBy(mode);
  });
  $scope.$watch('search.query', function (query) {
    annotationUI.setFilterQuery(query);
  });

  $scope.rootThread = function () {
    return rootThread.thread();
  };

  $scope.setCollapsed = function (id, collapsed) {
    annotationUI.setCollapsed(id, collapsed);
  };

  $scope.forceVisible = function (thread) {
    annotationUI.setForceVisible(thread.id, true);
    if (thread.parent) {
      annotationUI.setCollapsed(thread.parent.id, false);
    }
  };

  $scope.focus = focusAnnotation;
  $scope.scrollTo = scrollToAnnotation;

  $scope.hasFocus = function (annotation) {
    if (!annotation || !annotationUI.getState().focusedAnnotationMap) {
      return false;
    }
    return annotation.$$tag in annotationUI.getState().focusedAnnotationMap;
  };

  $scope.selectedAnnotationCount = function () {
    var selection = annotationUI.getState().selectedAnnotationMap;
    if (!selection) {
      return 0;
    }
    return Object.keys(selection).length;
  };

  $scope.selectedAnnotationUnavailable = function () {
    var selectedID = firstKey(annotationUI.getState().selectedAnnotationMap);
    return !isLoading() &&
           !!selectedID &&
           !annotationExists(selectedID);
  };

  $scope.shouldShowLoggedOutMessage = function () {
    // If user is not logged out, don't show CTA.
    if ($scope.auth.status !== 'signed-out') {
      return false;
    }

    // If user has not landed on a direct linked annotation
    // don't show the CTA.
    if (!settings.annotations) {
      return false;
    }

    // The user is logged out and has landed on a direct linked
    // annotation. If there is an annotation selection and that
    // selection is available to the user, show the CTA.
    var selectedID = firstKey(annotationUI.getState().selectedAnnotationMap);
    return !isLoading() &&
           !!selectedID &&
           annotationExists(selectedID);
  };

  $scope.isLoading = isLoading;

  var visibleCount = memoize(function (thread) {
    return thread.children.reduce(function (count, child) {
      return count + visibleCount(child);
    }, thread.visible ? 1 : 0);
  });

  $scope.visibleCount = function () {
    return visibleCount(rootThread.thread());
  };

  $scope.topLevelThreadCount = function () {
    return rootThread.thread().totalChildren;
  };

  /**
   * Return the offset between the top of the window and the top of the
   * first annotation card.
   */
  function cardListYOffset() {
    var cardListTopEl = document.querySelector('.js-thread-list-top');
    return cardListTopEl.getBoundingClientRect().top + window.pageYOffset;
  }

  /** Scroll the annotation with a given ID or $$tag into view. */
  function scrollIntoView(id) {
    var estimatedYOffset = visibleThreads.yOffsetOf(id);
    var estimatedPos = estimatedYOffset - cardListYOffset();

    window.scroll(0, estimatedPos);

    // As a result of scrolling the sidebar, the heights of some of the cards
    // above `id` might change because the initial estimate will be replaced by
    // the actual known height after a card is rendered.
    //
    // So we wait briefly after the view is scrolled then check whether the
    // estimated Y offset changed and if so, trigger scrolling again.
    scopeTimeout($scope, function () {
      var newYOffset = visibleThreads.yOffsetOf(id);
      if (newYOffset !== estimatedYOffset) {
        scrollIntoView(id);
      }
    }, 200);
  }

  $rootScope.$on(events.BEFORE_ANNOTATION_CREATED, function (event, data) {
    if (data.$highlight || (data.references && data.references.length > 0)) {
      return;
    }
    $scope.clearSelection();
    scrollIntoView(data.$$tag);
  });
};
