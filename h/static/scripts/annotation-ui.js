'use strict';

function value(selection) {
  if (Object.keys(selection).length) {
    return selection;
  } else {
    return null;
  }
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
module.exports = function () {
  return {
    visibleHighlights: false,

    // Contains a map of annotation tag:true pairs.
    focusedAnnotationMap: null,

    // Contains a map of annotation id:true pairs.
    selectedAnnotationMap: null,

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
     * @ngdoc method
     * @name annotationUI.selectAnnotations
     * @returns nothing
     * @description Takes an array of annotation objects and uses them to
     * set the selectedAnnotationMap property.
     */
    selectAnnotations: function (annotations) {
      var selection = {};
      for (var i = 0, annotation; i < annotations.length; i++) {
        annotation = annotations[i];
        selection[annotation.id] = true;
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
