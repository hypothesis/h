'use strict';

var Immutable = require('seamless-immutable');

function value(selection) {
  if (Object.keys(selection).length) {
    return Immutable(selection);
  } else {
    return null;
  }
}

function initialSelection(settings) {
  var selection = {};
  if (settings.annotations) {
    selection[settings.annotations] = true;
  }
  return value(selection);
}

function initialState(settings) {
  return Object.freeze({
    // List of all loaded annotations
    annotations: [],

    visibleHighlights: false,

    // Contains a map of annotation tag:true pairs.
    focusedAnnotationMap: null,

    // Contains a map of annotation id:true pairs.
    selectedAnnotationMap: initialSelection(settings),

    // Map of annotation IDs to expanded/collapsed state. For annotations not
    // present in the map, the default state is used which depends on whether
    // the annotation is a top-level annotation or a reply, whether it is
    // selected and whether it matches the current filter.
    expanded: {},

    // Set of IDs of annotations that have been explicitly shown
    // by the user even if they do not match the current search filter
    forceVisible: {},
  });
}

/**
 * Stores the UI state of the annotator in connected clients.
 *
 * This includes:
 * - The annotations that are currently loaded
 * - The IDs of annotations that are currently selected or focused
 * - The IDs of annotations whose conversation threads are expanded
 * - The state of the bucket bar
 *
 */
// @ngInject
module.exports = function (settings) {
  // List of subscribers listening for changes to the UI state
  var listeners = [];
  var state = initialState(settings);

  // Update the UI state and notify subscribers of the change.
  function setState(newState) {
    state = Object.freeze(Object.assign({}, state, newState));
    listeners.forEach(function (listener) {
      listener();
    });
  }

  function subscribe(listener) {
    listeners.push(listener);
    return function () {
      listeners = listeners.filter(function (other) {
        return other !== listener;
      });
    };
  }

  return {
    /**
     * Return the current UI state of the sidebar. This should not be modified
     * directly but only though the helper methods below.
     */
    getState: function () {
      return state;
    },

    /** Listen for changes to the UI state of the sidebar. */
    subscribe: subscribe,

    /**
     * Sets whether annotation highlights in connected documents are shown
     * or not.
     */
    setShowHighlights: function (show) {
      setState({visibleHighlights: show});
    },

    /**
     * Sets which annotations are currently focused.
     *
     * @param {Array<Annotation>} annotations
     */
    focusAnnotations: function (annotations) {
      var selection = {};
      for (var i = 0, annotation; i < annotations.length; i++) {
        annotation = annotations[i];
        selection[annotation.$$tag] = true;
      }
      setState({focusedAnnotationMap: value(selection)});
    },

    /**
     * Return true if any annotations are currently selected.
     */
    hasSelectedAnnotations: function () {
      return !!state.selectedAnnotationMap;
    },

    /**
     * Sets whether replies to the annotation with ID `id` are collapsed.
     *
     * @param {string} id - Annotation ID
     * @param {boolean} collapsed
     */
    setCollapsed: function (id, collapsed) {
      var expanded = Object.assign({}, state.expanded);
      expanded[id] = !collapsed;
      setState({expanded: expanded});
    },

    /**
     * Sets whether a given annotation should be visible, even if it does not
     * match the current search query.
     *
     * @param {string} id - Annotation ID
     * @param {boolean} visible
     */
    setForceVisible: function (id, visible) {
      var forceVisible = Object.assign({}, state.forceVisible);
      forceVisible[id] = visible;
      setState({forceVisible: forceVisible});
    },

    /**
     * Clear the set of annotations which have been explicitly shown by
     * setForceVisible()
     */
    clearForceVisible: function () {
      setState({forceVisible: {}});
    },

    /**
     * Returns true if the annotation with the given `id` is selected.
     */
    isAnnotationSelected: function (id) {
      return (state.selectedAnnotationMap || {}).hasOwnProperty(id);
    },

    /**
     * Set the currently selected annotation IDs.
     *
     * @param {Array<string|{id:string}>} annotations - Annotations or IDs
     *        of annotations to select.
     */
    selectAnnotations: function (annotations) {
      var selection = {};
      for (var i = 0; i < annotations.length; i++) {
        if (typeof annotations[i] === 'string') {
          selection[annotations[i]] = true;
        } else {
          selection[annotations[i].id] = true;
        }
      }
      setState({selectedAnnotationMap: value(selection)});
    },

    /** Toggle whether annotations are selected or not. */
    xorSelectedAnnotations: function (annotations) {
      var selection = Object.assign({}, state.selectedAnnotationMap);
      for (var i = 0, annotation; i < annotations.length; i++) {
        annotation = annotations[i];
        var id = annotation.id;
        if (selection[id]) {
          delete selection[id];
        } else {
          selection[id] = true;
        }
      }
      setState({selectedAnnotationMap: value(selection)});
    },

    /** De-select an annotation. */
    removeSelectedAnnotation: function (annotation) {
      var selection = Object.assign({}, state.selectedAnnotationMap);
      if (selection) {
        delete selection[annotation.id];
        setState({selectedAnnotationMap: value(selection)});
      }
    },

    /** De-select all annotations. */
    clearSelectedAnnotations: function () {
      setState({selectedAnnotationMap: null});
    },

    /** Add annotations to the currently displayed set. */
    addAnnotations: function (annotations) {
      setState({annotations: state.annotations.concat(annotations)});
    },

    /** Remove annotations from the currently displayed set. */
    removeAnnotations: function (annotations) {
      var idsAndTags = annotations.reduce(function (map, annot) {
        var id = annot.id || annot.$$tag;
        map[id] = true;
        return map;
      }, {});
      var newAnnotations = state.annotations.filter(function (annot) {
        var id = annot.id || annot.$$tag;
        return !idsAndTags[id];
      });
      setState({annotations: newAnnotations});
    },

    /** Set the currently displayed annotations to the empty set. */
    clearAnnotations: function () {
      setState({annotations: []});
    },
  };
};
