'use strict';

var buildThread = require('./build-thread');
var events = require('./events');
var metadata = require('./annotation-metadata');

function truthyKeys(map) {
  return Object.keys(map).filter(function (k) {
    return !!map[k];
  });
}

// Mapping from sort order name to a less-than predicate
// function for comparing annotations to determine their sort order.
var sortFns = {
  'Newest': function (a, b) {
    return a.updated > b.updated;
  },
  'Oldest': function (a, b) {
    return a.updated < b.updated;
  },
  'Location': function (a, b) {
    return metadata.location(a) < metadata.location(b);
  },
};

/**
 * Root conversation thread for the sidebar and stream.
 *
 * Listens for annotations being loaded, created and unloaded and
 * builds a conversation thread.
 *
 * The thread is sorted and filtered according to
 * current sort and filter settings.
 *
 * The root thread is then displayed by viewer.html
 */
// @ngInject
module.exports = function ($rootScope, annotationUI, searchFilter, viewFilter) {
  var thread;

  var sortFn = sortFns.Location;
  var searchQuery;

  /**
   * Rebuild the root conversation thread. This should be called
   * whenever the set of annotations to render or the sort/search/filter
   * settings change.
   */
  function rebuildRootThread() {
    var filters;
    if (searchQuery) {
      // TODO - Only regenerate the filter function when the search
      // query changes
      filters = searchFilter.generateFacetedFilter(searchQuery);
    }

    var filterFn;
    if (searchQuery) {
      filterFn = function (annot) {
        return viewFilter.filter([annot], filters).length > 0;
      };
    }

    // Get the currently loaded annotations and the set of inputs which
    // determines what is visible and build the visible thread structure
    var state = annotationUI.getState();
    thread = buildThread(state.annotations, {
      forceVisible: truthyKeys(state.forceVisible),
      expanded: state.expanded,
      selected: truthyKeys(state.selectedAnnotationMap || {}),
      sortCompareFn: sortFn,
      filterFn: filterFn,
    });
  }
  rebuildRootThread();
  annotationUI.subscribe(rebuildRootThread);

  // Listen for annotations being created or loaded
  // and show them in the UI
  var loadEvents = [events.BEFORE_ANNOTATION_CREATED,
                    events.ANNOTATION_CREATED,
                    events.ANNOTATIONS_LOADED];
  loadEvents.forEach(function (event) {
    $rootScope.$on(event, function (event, annotation) {
      var annotations = [].concat(annotation);

      // Remove any annotations which are already loaded
      annotationUI.removeAnnotations(annotations);

      // Add the new annotations
      annotationUI.addAnnotations(annotations);

      // Ensure that newly created annotations are always visible
      if (event.name === events.BEFORE_ANNOTATION_CREATED) {
        (annotation.references || []).forEach(function (parent) {
          annotationUI.setCollapsed(parent, false);
        });
      }
    });
  });

  // Remove any annotations that are deleted or unloaded
  $rootScope.$on(events.ANNOTATION_DELETED, function (event, annotation) {
    annotationUI.removeAnnotations([annotation]);
    annotationUI.removeSelectedAnnotation(annotation);
  });
  $rootScope.$on(events.ANNOTATIONS_UNLOADED, function (event, annotations) {
    annotationUI.removeAnnotations(annotations);
  });

  return {
    /**
     * Rebuild the conversation thread based on the currently loaded annotations
     * and search/sort/filter settings.
     */
    rebuild: rebuildRootThread,

    /**
     * Returns the current root conversation thread.
     * @return {Thread}
     */
    thread: function () {
      return thread;
    },

    /**
     * Set the sort order for annotations.
     * @param {'Location'|'Newest'|'Oldest'} mode
     */
    sortBy: function (mode) {
      if (!sortFns[mode]) {
        throw new Error('Unknown sort mode: ' + mode);
      }
      sortFn = sortFns[mode];
      rebuildRootThread();
    },

    /**
     * Set the query to use when filtering annotations.
     * @param {string} query - The filter query
     */
    setSearchQuery: function (query) {
      searchQuery = query;
      annotationUI.clearForceVisible();
      rebuildRootThread();
    },
  };
};
