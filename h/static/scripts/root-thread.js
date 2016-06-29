'use strict';

var buildThread = require('./build-thread');
var events = require('./events');
var memoize = require('./util/memoize');
var metadata = require('./annotation-metadata');
var uiConstants = require('./ui-constants');

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
 * This performs two functions:
 *
 * 1. It listens for annotations being loaded, created and unloaded and
 *    dispatches annotationUI.{addAnnotations|removeAnnotations} actions.
 * 2. Listens for changes in the UI state and rebuilds the root conversation
 *    thread.
 *
 * The root thread is then displayed by viewer.html
 */
// @ngInject
function RootThread($rootScope, annotationUI, features, searchFilter, viewFilter) {

  /**
   * Build the root conversation thread from the given UI state.
   *
   * @param state - The current UI state (loaded annotations, sort mode,
   *        filter settings etc.)
   */
  function buildRootThread(state) {
    var sortFn = sortFns[state.sortKey];

    var filterFn;
    if (state.filterQuery) {
      var filters = searchFilter.generateFacetedFilter(state.filterQuery);
      filterFn = function (annot) {
        return viewFilter.filter([annot], filters).length > 0;
      };
    }

    var threadFilterFn;
    if (features.flagEnabled('selection_tabs') && !state.filterQuery) {
      threadFilterFn = function (thread) {
        if (state.selectedTab === uiConstants.TAB_ANNOTATIONS) {
          return thread.annotation && metadata.isAnnotation(thread.annotation);
        } else if (state.selectedTab === uiConstants.TAB_NOTES) {
          return thread.annotation && metadata.isPageNote(thread.annotation);
        }
      };
    }

    // Get the currently loaded annotations and the set of inputs which
    // determines what is visible and build the visible thread structure
    return buildThread(state.annotations, {
      forceVisible: truthyKeys(state.forceVisible),
      expanded: state.expanded,
      highlighted: state.highlighted,
      selected: truthyKeys(state.selectedAnnotationMap || {}),
      sortCompareFn: sortFn,
      filterFn: filterFn,
      threadFilterFn: threadFilterFn,
    });
  }

  // Listen for annotations being created or loaded
  // and show them in the UI.
  //
  // Note: These events could all be converted into actions that are handled by
  // the Redux store in annotationUI.
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

        // If the annotation is of type note or annotation, make sure
        // the appropriate tab is selected. If it is of type reply, user
        // stays in the selected tab.
        if (metadata.isPageNote(annotation)) {
          annotationUI.selectTab(uiConstants.TAB_NOTES);
        } else if (metadata.isAnnotation(annotation)) {
          annotationUI.selectTab(uiConstants.TAB_ANNOTATIONS);
        }

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

  /**
   * Build the root conversation thread from the given UI state.
   * @return {Thread}
   */
  this.thread = memoize(buildRootThread);
}

module.exports = RootThread;
