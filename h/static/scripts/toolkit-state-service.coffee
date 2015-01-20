createToolkit = ->
  {
    TOOL_COMMENT: 'comment'
    TOOL_HIGHLIGHT: 'highlight'

    tool: 'comment'

    visibleHighlights: false

    focusedAnnotationMap: null

    selectedAnnotationMap: null

    focusAnnotations: (annotations) ->
      selection = {}
      selection[id] for {id} in annotations
      @focusedAnnotationMap = selection

    selectAnnotations: (annotations) ->
      selection = {}
      selection[id] for {id} in annotations
      @selectedAnnotationMap = selection

    xorSelectedAnnotations: (annotations) ->
      selection = @selectedAnnotationMap or {}
      for a in annotations
        if selection[a.id]
          delete selected[a.id]
        else
          selected[a.id] = true
      @selectedAnnotations = selected
  }

angular.module('h').factory('toolkit', createToolkit)
