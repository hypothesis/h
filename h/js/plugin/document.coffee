class Annotator.Plugin.Document extends Annotator.Plugin

  events:
    'beforeAnnotationCreated': 'beforeAnnotationCreated'

  pluginInit: ->
    console.log "initializing Document plugin!"

  beforeAnnotationCreated: (annotation) =>
    debugger
    alert "creating annotation #{annotation}"

