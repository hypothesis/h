angular = require('angular')
mail = require('./vendor/jwz')

# The threading service provides the model for the currently loaded
# set of annotations, structured as a tree of annotations and replies.
#
# The service listens for events when annotations are loaded, unloaded,
# created or deleted and updates the tree model in response.
#
# The conversion of a flat list of incoming messages into a tree structure
# with replies nested under their parents
# uses an implementation of the `jwz` message threading algorithm
# (see https://www.jwz.org/doc/threading.html and the JS port
#  at https://github.com/maxogden/conversationThreading-js).
#
# The 'Threading' service "inherits" from 'mail.messageThread'
#
module.exports = class Threading
  root: null

  this.$inject = ['$rootScope']
  constructor: ($rootScope) ->
    # XXX: gross hack to inherit from messageThread, which doesn't have an
    # accessible prototype.
    thread = new mail.messageThread()
    threadInheritedProperties = {}
    for key in Object.getOwnPropertyNames(thread) when not this[key]?
      descriptor = Object.getOwnPropertyDescriptor(thread, key)
      threadInheritedProperties[key] = descriptor
    Object.defineProperties(this, threadInheritedProperties)

    # Create a root container.
    @root = mail.messageContainer()
    $rootScope.$on('beforeAnnotationCreated', this.beforeAnnotationCreated)
    $rootScope.$on('annotationCreated', this.annotationCreated)
    $rootScope.$on('annotationDeleted', this.annotationDeleted)
    $rootScope.$on('annotationsLoaded', this.annotationsLoaded)

  # TODO: Refactor the jwz API for progressive updates.
  # Right now the idTable is wiped when `messageThread.thread()` is called and
  # empty containers are pruned. We want to show empties so that replies attach
  # to missing parents and threads can be updates as new data arrives.
  thread: (messages) ->
    for message in messages
      # Get or create a thread to contain the annotation
      if message.id
        thread = (this.getContainer message.id)
        thread.message = message
      else
        # XXX: relies on outside code to update the idTable if the message
        # later acquires an id.
        thread = mail.messageContainer(message)

      prev = @root

      references = message.references or []
      if typeof(message.references) == 'string'
        references = [references]

      # Build out an ancestry from the root
      for reference in references
        container = this.getContainer(reference)
        unless container.parent? or container.hasDescendant(prev)  # no cycles
          prev.addChild(container)
        prev = container

      # Attach the thread at its leaf location
      unless thread.hasDescendant(prev)  # no cycles
        do ->
          for child in prev.children when child.message is message
            return  # no dupes
          prev.addChild(thread)

    this.pruneEmpties(@root)
    @root

  # Returns a flat list of every annotation that is currently loaded
  # in the thread
  annotationList: ->
    (message for id, {message} of @idTable when message)

  pruneEmpties: (parent) ->
    for container in parent.children
      this.pruneEmpties(container)

      if !container.message && container.children.length == 0
        parent.removeChild(container)

  beforeAnnotationCreated: (event, annotation) =>
    this.thread([annotation])

  annotationCreated: (event, annotation) =>
    references = annotation.references or []
    if typeof(annotation.references) == 'string' then references = []
    ref = references[references.length-1]
    parent = if ref then @idTable[ref] else @root
    for child in (parent.children or []) when child.message is annotation
      @idTable[annotation.id] = child
      break

  annotationDeleted: (event, annotation) =>
    if this.idTable[annotation.id]
      container = this.idTable[annotation.id]
      container.message = null
      delete this.idTable[annotation.id]
      this.pruneEmpties(@root)
    else
      if annotation.references
        refs = annotation.references
        unless  angular.isArray(refs) then refs = [refs]
        parentRef = refs[refs.length-1]
        parent = this.idTable[parentRef]
      else
        parent = @root
      for child in parent.children when child.message is annotation
        child.message = null
        this.pruneEmpties(@root)
        break

  annotationsLoaded: (event, annotations) =>
    messages = (@root.flattenChildren() or []).concat(annotations)
    this.thread(messages)
