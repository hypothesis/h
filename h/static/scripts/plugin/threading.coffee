class Annotator.Plugin.Threading extends Annotator.Plugin
  # Mix in message thread properties into the prototype. The body of the
  # class will overwrite any methods applied here.
  messageThread = mail.messageThread()
  $.extend(this.prototype, messageThread)

  events:
    'beforeAnnotationCreated': 'beforeAnnotationCreated'
    'annotationDeleted': 'annotationDeleted'
    'annotationsLoaded': 'annotationsLoaded'

  root: null

  pluginInit: ->
    # Create a root container.
    @root = mail.messageContainer()

    # Set to true if empty parent annotations should be removed.
    @shouldRemoveEmptyParents = false

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

  pruneEmpties: (parent) ->
    for container in parent.children
      this.pruneEmpties(container)

      if !container.message && container.children.length == 0
        parent.removeChild(container)

      else if @shouldRemoveEmptyParents
        this.pruneParents(container)

  # Removes empty root messages and promotes the child up a level. This
  # is used on the standalone annotation page to show a reply in a thread
  # as an annotation card.
  pruneParents: (container) ->
    hasParentWithMessage = (c) ->
      while c = c.parent
        return true if c.message
      return false

    if !container.message && container.children.length > 0
      if !hasParentWithMessage(container)
        this.promoteChildren(container.parent, container)

  beforeAnnotationCreated: (annotation) =>
    this.thread([annotation])

  annotationDeleted: ({id}) =>
    container = this.getContainer id
    container.message = null
    this.pruneEmpties(@root)

  annotationsLoaded: (annotations) =>
    messages = (@root.flattenChildren() or []).concat(annotations)
    this.thread(messages)
