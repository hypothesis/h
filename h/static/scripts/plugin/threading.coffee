class Annotator.Plugin.Threading extends Annotator.Plugin
  $.extend(this.prototype, mail.messageThread())

  events:
    'beforeAnnotationCreated': 'beforeAnnotationCreated'
    'annotationDeleted': 'annotationDeleted'
    'annotationsLoaded': 'annotationsLoaded'

  root: null

  pluginInit: ->
    # Create a root container.
    @root = mail.messageContainer()

    # Mix in message thread properties, preserving local overrides.
    $.extend(this, thread: this.thread)

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

  beforeAnnotationCreated: (annotation) =>
    this.thread([annotation])

  annotationDeleted: ({id}) =>
    container = this.getContainer id
    container.message = null
    this.pruneEmpties(@root)

  annotationsLoaded: (annotations) =>
    messages = (@root.flattenChildren() or []).concat(annotations)
    this.thread(messages)
