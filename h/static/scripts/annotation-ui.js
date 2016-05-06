'use strict';

var immutable = require('seamless-immutable');
var redux = require('redux');

function value(selection) {
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
  return value(selection);
}

function initialState(settings) {
  return Object.freeze({
    visibleHighlights: false,

    // Contains a map of annotation tag:true pairs.
    focusedAnnotationMap: null,

    // Contains a map of annotation id:true pairs.
    selectedAnnotationMap: initialSelection(settings),
  });
}

var types = {
  SELECT_ANNOTATIONS: 'SELECT_ANNOTATIONS',
  FOCUS_ANNOTATIONS: 'FOCUS_ANNOTATIONS',
  SET_HIGHLIGHTS_VISIBLE: 'SET_HIGHLIGHTS_VISIBLE',
};

function reducer(state, action) {
  switch (action.type) {
    case types.SELECT_ANNOTATIONS:
      return Object.assign({}, state, {selectedAnnotationMap: action.selection});
    case types.FOCUS_ANNOTATIONS:
      return Object.assign({}, state, {focusedAnnotationMap: action.focused});
    case types.SET_HIGHLIGHTS_VISIBLE:
      return Object.assign({}, state, {visibleHighlights: action.visible});
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
      selection: value(annotations),
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
        focused: value(selection),
      });
    },

    /**
     * Return true if any annotations are currently selected.
     */
    hasSelectedAnnotations: function () {
      return !!store.getState().selectedAnnotationMap;
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
    xorSelectedAnnotations: function (annotations) {
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
  };
};
