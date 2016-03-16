'use strict';

function value(selection) {
  if (Object.keys(selection).length) {
    return Object.freeze(selection);
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

/**
 * Stores the UI state of the annotator in connected clients.
 *
 * This includes:
 * - The set of annotations that are currently selected
 * - The annotation(s) that are currently hovered/focused
 * - The state of the bucket bar
 *
 */

// @ngInject
module.exports = function (settings) {
  return {
    visibleHighlights: false,

    // Contains a map of annotation tag:true pairs.
    focusedAnnotationMap: null,

    // Contains a map of annotation id:true pairs.
    selectedAnnotationMap: initialSelection(settings),

    /**
     * @ngdoc method
     * @name annotationUI.focusedAnnotations
     * @returns nothing
     * @description Takes an array of annotations and uses them to set
     * the focusedAnnotationMap.
     */
    focusAnnotations: function (annotations) {
      var selection = {};
      for (var i = 0, annotation; i < annotations.length; i++) {
        annotation = annotations[i];
        selection[annotation.$$tag] = true;
      }
      this.focusedAnnotationMap = value(selection);
    },

    /**
     * @ngdoc method
     * @name annotationUI.hasSelectedAnnotations
     * @returns true if there are any selected annotations.
     */
    hasSelectedAnnotations: function () {
      return !!this.selectedAnnotationMap;
    },

    /**
     * @ngdoc method
     * @name annotationUI.isAnnotationSelected
     * @returns true if the provided annotation is selected.
     */
    isAnnotationSelected: function (id) {
      return (this.selectedAnnotationMap || {}).hasOwnProperty(id);
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
      this.selectedAnnotationMap = value(selection);
    },

    /**
     * @ngdoc method
     * @name annotationUI.xorSelectedAnnotations()
     * @returns nothing
     * @description takes an array of annotations and adds them to the
     * selectedAnnotationMap if not present otherwise removes them.
     */
    xorSelectedAnnotations: function (annotations) {
      var selection = Object.assign({}, this.selectedAnnotationMap);
      for (var i = 0, annotation; i < annotations.length; i++) {
        annotation = annotations[i];
        var id = annotation.id;
        if (selection[id]) {
          delete selection[id];
        } else {
          selection[id] = true;
        }
      }
      this.selectedAnnotationMap = value(selection);
    },

    /**
     * @ngdoc method
     * @name annotationUI.removeSelectedAnnotation()
     * @returns nothing
     * @description removes an annotation from the current selection.
     */
    removeSelectedAnnotation: function (annotation) {
      var selection = Object.assign({}, this.selectedAnnotationMap);
      if (selection) {
        delete selection[annotation.id];
        this.selectedAnnotationMap = value(selection);
      }
    },

    /**
     * @ngdoc method
     * @name annotationUI.clearSelectedAnnotations()
     * @returns nothing
     * @description removes all annotations from the current selection.
     */
    clearSelectedAnnotations: function () {
      this.selectedAnnotationMap = null;
    }
  };
};
