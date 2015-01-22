# Holds the current state between the current state of the annotator in the
# attached iframes for display in the sidebar. This covers both tool and
# rendered state such as selected highlights.
createAnnotationUI = ->
  {
    TOOL_COMMENT: 'comment'
    TOOL_HIGHLIGHT: 'highlight'

    tool: 'comment'

    visibleHighlights: false

    focusedAnnotationMap: null

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
      selection[id] = true for {id} in annotations
      @focusedAnnotationMap = selection

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
      @selectedAnnotationMap = selection

    ###*
    # @ngdoc method
    # @name annotationUI.xorSelectedAnnotations()
    # @returns nothing
    # @description takes an array of annotations and adds them to the
    # selectedAnnotationMap if not present otherwise removes them.
    ###
    xorSelectedAnnotations: (annotations) ->
      selection = @selectedAnnotationMap or {}
      for {id} in annotations
        if selection[id]
          delete selection[id]
        else
          selection[id] = true
      @selectedAnnotations = selection
  }

angular.module('h').factory('annotationUI', createAnnotationUI)
