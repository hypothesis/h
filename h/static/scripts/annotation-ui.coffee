value = (selection) ->
  if Object.keys(selection).length then selection else null

# Holds the current state between the current state of the annotator in the
# attached iframes for display in the sidebar. This covers both tool and
# rendered state such as selected highlights.
module.exports = ->
  visibleHighlights: false

  # Contains a map of annotation tag:true pairs.
  focusedAnnotationMap: null

  # Contains a map of annotation id:true pairs.
  selectedAnnotationMap: null

  ###*
  # @ngdoc method
  # @name annotationUI.focusedAnnotations
  # @returns nothing
  # @description Takes an array of annotations and uses them to set
  # the focusedAnnotationMap.
  ###
  focusAnnotations: (annotations) ->
    selection = {}
    selection[$$tag] = true for {$$tag} in annotations
    @focusedAnnotationMap = value(selection)

  ###*
  # @ngdoc method
  # @name annotationUI.hasSelectedAnnotations
  # @returns true if there are any selected annotations.
  ###
  hasSelectedAnnotations: ->
    !!@selectedAnnotationMap

  ###*
  # @ngdoc method
  # @name annotationUI.isAnnotationSelected
  # @returns true if the provided annotation is selected.
  ###
  isAnnotationSelected: (id) ->
    !!@selectedAnnotationMap?[id]

  ###*
  # @ngdoc method
  # @name annotationUI.selectAnnotations
  # @returns nothing
  # @description Takes an array of annotation objects and uses them to
  # set the selectedAnnotationMap property.
  ###
  selectAnnotations: (annotations) ->
    selection = {}
    selection[id] = true for {id} in annotations
    @selectedAnnotationMap = value(selection)

  ###*
  # @ngdoc method
  # @name annotationUI.xorSelectedAnnotations()
  # @returns nothing
  # @description takes an array of annotations and adds them to the
  # selectedAnnotationMap if not present otherwise removes them.
  ###
  xorSelectedAnnotations: (annotations) ->
    selection = angular.extend({}, @selectedAnnotationMap)
    for {id} in annotations
      if selection[id]
        delete selection[id]
      else
        selection[id] = true
    @selectedAnnotationMap = value(selection)

  ###*
  # @ngdoc method
  # @name annotationUI.removeSelectedAnnotation()
  # @returns nothing
  # @description removes an annotation from the current selection.
  ###
  removeSelectedAnnotation: (annotation) ->
    selection = angular.extend({}, @selectedAnnotationMap)
    if selection
      delete selection[annotation.id]
      @selectedAnnotationMap = value(selection)

  ###*
  # @ngdoc method
  # @name annotationUI.clearSelectedAnnotations()
  # @returns nothing
  # @description removes all annotations from the current selection.
  ###
  clearSelectedAnnotations: ->
    @selectedAnnotationMap = null
