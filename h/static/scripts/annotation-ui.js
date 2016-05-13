'use strict';

/**
 * AnnotationUI provides the central store of UI state for the application,
 * using [Redux](http://redux.js.org/).
 *
 * Redux is used to provide a predictable way of updating UI state and
 * responding to UI state changes.
 */

var immutable = require('seamless-immutable');
var redux = require('redux');

function freeze(selection) {
  if (Object.keys(selection).length) {
    return immutable(selection);
  } else {
    return null;
  }
}

function initialSelection(settings) {
  var selection = {};
  if (settings.annotations) {
    selection[settings.annotations] = true;
  }
  return freeze(selection);
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

var types = {
  SELECT_ANNOTATIONS: 'SELECT_ANNOTATIONS',
  FOCUS_ANNOTATIONS: 'FOCUS_ANNOTATIONS',
  SET_HIGHLIGHTS_VISIBLE: 'SET_HIGHLIGHTS_VISIBLE',
  SET_FORCE_VISIBLE: 'SET_FORCE_VISIBLE',
  SET_EXPANDED: 'SET_EXPANDED',
  ADD_ANNOTATIONS: 'ADD_ANNOTATIONS',
  REMOVE_ANNOTATIONS: 'REMOVE_ANNOTATIONS',
  CLEAR_ANNOTATIONS: 'CLEAR_ANNOTATIONS',
};

function excludeAnnotations(current, annotations) {
  var idsAndTags = annotations.reduce(function (map, annot) {
    var id = annot.id || annot.$$tag;
    map[id] = true;
    return map;
  }, {});
  return current.filter(function (annot) {
    var id = annot.id || annot.$$tag;
    return !idsAndTags[id];
  });
}

function annotationsReducer(state, action) {
  switch (action.type) {
    case types.ADD_ANNOTATIONS:
      return Object.assign({}, state,
        {annotations: state.annotations.concat(action.annotations)});
    case types.REMOVE_ANNOTATIONS:
      return Object.assign({}, state,
        {annotations: excludeAnnotations(state.annotations, action.annotations)});
    case types.CLEAR_ANNOTATIONS:
      return Object.assign({}, state, {annotations: []});
    default:
      return state;
  }
}

function reducer(state, action) {
  state = annotationsReducer(state, action);

  switch (action.type) {
    case types.SELECT_ANNOTATIONS:
      return Object.assign({}, state, {selectedAnnotationMap: action.selection});
    case types.FOCUS_ANNOTATIONS:
      return Object.assign({}, state, {focusedAnnotationMap: action.focused});
    case types.SET_HIGHLIGHTS_VISIBLE:
      return Object.assign({}, state, {visibleHighlights: action.visible});
    case types.SET_FORCE_VISIBLE:
      return Object.assign({}, state, {forceVisible: action.forceVisible});
    case types.SET_EXPANDED:
      return Object.assign({}, state, {expanded: action.expanded});
    default:
      return state;
  }
}

/**
 * Stores the UI state of the annotator in connected clients.
 *
 * This includes:
 * - The IDs of annotations that are currently selected or focused
 * - The state of the bucket bar
 *
 */
// @ngInject
module.exports = function (settings) {
  var store = redux.createStore(reducer, initialState(settings));

  function select(annotations) {
    store.dispatch({
      type: types.SELECT_ANNOTATIONS,
      selection: freeze(annotations),
    });
  }

  return {
    /**
     * Return the current UI state of the sidebar. This should not be modified
     * directly but only though the helper methods below.
     */
    getState: store.getState,

    /** Listen for changes to the UI state of the sidebar. */
    subscribe: store.subscribe,

    /**
     * Sets whether annotation highlights in connected documents are shown
     * or not.
     */
    setShowHighlights: function (show) {
      store.dispatch({
        type: types.SET_HIGHLIGHTS_VISIBLE,
        visible: show,
      });
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
      store.dispatch({
        type: types.FOCUS_ANNOTATIONS,
        focused: freeze(selection),
      });
    },

    /**
     * Return true if any annotations are currently selected.
     */
    hasSelectedAnnotations: function () {
      return !!store.getState().selectedAnnotationMap;
    },

    /**
     * Sets whether replies to the annotation with ID `id` are collapsed.
     *
     * @param {string} id - Annotation ID
     * @param {boolean} collapsed
     */
    setCollapsed: function (id, collapsed) {
      var expanded = Object.assign({}, store.getState().expanded);
      expanded[id] = !collapsed;
      store.dispatch({
        type: types.SET_EXPANDED,
        expanded: expanded,
      });
    },

    /**
     * Sets whether a given annotation should be visible, even if it does not
     * match the current search query.
     *
     * @param {string} id - Annotation ID
     * @param {boolean} visible
     */
    setForceVisible: function (id, visible) {
      var forceVisible = Object.assign({}, store.getState().forceVisible);
      forceVisible[id] = visible;
      store.dispatch({
        type: types.SET_FORCE_VISIBLE,
        forceVisible: forceVisible,
      });
    },

    /**
     * Clear the set of annotations which have been explicitly shown by
     * setForceVisible()
     */
    clearForceVisible: function () {
      store.dispatch({
        type: types.SET_FORCE_VISIBLE,
        forceVisible: {},
      });
    },

    /**
     * Returns true if the annotation with the given `id` is selected.
     */
    isAnnotationSelected: function (id) {
      return (store.getState().selectedAnnotationMap || {}).hasOwnProperty(id);
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
      select(selection);
    },

    /** Toggle whether annotations are selected or not. */
    toggleSelectedAnnotations: function (annotations) {
      var selection = Object.assign({}, store.getState().selectedAnnotationMap);
      for (var i = 0, annotation; i < annotations.length; i++) {
        annotation = annotations[i];
        var id = annotation.id;
        if (selection[id]) {
          delete selection[id];
        } else {
          selection[id] = true;
        }
      }
      select(selection);
    },

    /** De-select an annotation. */
    removeSelectedAnnotation: function (annotation) {
      var selection = Object.assign({}, store.getState().selectedAnnotationMap);
      if (selection) {
        delete selection[annotation.id];
        select(selection);
      }
    },

    /** De-select all annotations. */
    clearSelectedAnnotations: function () {
      select({});
    },

    /** Add annotations to the currently displayed set. */
    addAnnotations: function (annotations) {
      store.dispatch({
        type: 'ADD_ANNOTATIONS',
        annotations: annotations,
      });
    },

    /** Remove annotations from the currently displayed set. */
    removeAnnotations: function (annotations) {
      store.dispatch({
        type: types.REMOVE_ANNOTATIONS,
        annotations: annotations,
      });
    },

    /** Set the currently displayed annotations to the empty set. */
    clearAnnotations: function () {
      store.dispatch({type: types.CLEAR_ANNOTATIONS});
    },
  };
};
