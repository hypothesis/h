class Annotator.Plugin.Threading extends Annotator.Plugin
  # These events maintain the awareness of annotations between the two
  # communicating annotators.
  events:
    'annotationDeleted': 'annotationDeleted'
    'annotationsLoaded': 'annotationsLoaded'
    'beforeAnnotationCreated': 'beforeAnnotationCreated'

  # Cache of annotations which have crossed the bridge for fast, encapsulated
  # association of annotations received in arguments to window-local copies.
  cache: {}

  pluginInit: ->
    @annotator.threading = mail.messageThread()

  thread: (annotation) ->
    # Get or create a thread to contain the annotation
    thread = (@annotator.threading.getContainer annotation.id)
    thread.message = annotation

    # Attach the thread to its parent, if any.
    if annotation.references?.length
      prev = annotation.references[annotation.references.length-1]
      @annotator.threading.getContainer(prev).addChild thread

    # Expose the thread to the annotation
    Object.defineProperty annotation, 'thread',
        configurable: true
        enumerable: false
        writable: true
        value: thread

    # Update the id table
    @annotator.threading.idTable[annotation.id] = thread

    thread

  annotationDeleted: (annotation) =>
    thread = (@annotator.threading.getContainer annotation.id)
    delete @annotator.threading.idTable[annotation.id]
    delete annotation.thread  # Break cyclic reference
    thread.message = null
    if thread.parent? then @annotator.threading.pruneEmpties thread.parent

  annotationsLoaded: (annotations) =>
    @annotator.threading.thread annotations
    this.thread a for a in annotations

  beforeAnnotationCreated: (annotation) =>
    # Assign temporary id. Threading relies on the id.
    Object.defineProperty annotation, 'id',
      configurable: true
      enumerable: false
      writable: true
      value: window.btoa Math.random()
    this.thread annotation
