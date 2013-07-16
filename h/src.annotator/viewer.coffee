# Public: Creates an element for viewing annotations.
class Annotator.Viewer extends Annotator.Widget

  # Events to be bound to the @element.
  events:
    ".annotator-edit click":   "onEditClick"
    ".annotator-delete click": "onDeleteClick"

  # Classes for toggling annotator state.
  classes:
    hide: 'annotator-hide'
    showControls: 'annotator-visible'

  # HTML templates for @element and @item properties.
  html:
    element:"""
            <div class="annotator-outer annotator-viewer">
              <ul class="annotator-widget annotator-listing"></ul>
            </div>
            """
    item:   """
            <li class="annotator-annotation annotator-item">
              <span class="annotator-controls">
                <a href="#" title="View as webpage" class="annotator-link">View as webpage</a>
                <button title="Edit" class="annotator-edit">Edit</button>
                <button title="Delete" class="annotator-delete">Delete</button>
              </span>
            </li>
            """

  # Configuration options
  options:
    readOnly: false # Start the viewer in read-only mode. No controls will be shown.

  # Public: Creates an instance of the Viewer object. This will create the
  # @element from the @html.element string and set up all events.
  #
  # options - An Object literal containing options.
  #
  # Examples
  #
  #   # Creates a new viewer, adds a custom field and displays an annotation.
  #   viewer = new Annotator.Viewer()
  #   viewer.addField({
  #     load: someLoadCallback
  #   })
  #   viewer.load(annotation)
  #
  # Returns a new Viewer instance.
  constructor: (options) ->
    super $(@html.element)[0], options

    @item   = $(@html.item)[0]
    @fields = []
    @annotations = []

  # Public: Displays the Viewer and first the "show" event. Can be used as an
  # event callback and will call Event#preventDefault() on the supplied event.
  #
  # event - Event object provided if method is called by event
  #         listener (default:undefined)
  #
  # Examples
  #
  #   # Displays the editor.
  #   viewer.show()
  #
  #   # Displays the viewer on click (prevents default action).
  #   $('a.show-viewer').bind('click', viewer.show)
  #
  # Returns itself.
  show: (event) =>
    Annotator.Util.preventEventDefault event

    controls = @element
      .find('.annotator-controls')
      .addClass(@classes.showControls)
    setTimeout((=> controls.removeClass(@classes.showControls)), 500)

    @element.removeClass(@classes.hide)
    this.checkOrientation().publish('show')

  # Public: Checks to see if the Viewer is currently displayed.
  #
  # Examples
  #
  #   viewer.show()
  #   viewer.isShown() # => Returns true
  #
  #   viewer.hide()
  #   viewer.isShown() # => Returns false
  #
  # Returns true if the Viewer is visible.
  isShown: ->
    not @element.hasClass(@classes.hide)

  # Public: Hides the Editor and fires the "hide" event. Can be used as an event
  # callback and will call Event#preventDefault() on the supplied event.
  #
  # event - Event object provided if method is called by event
  #         listener (default:undefined)
  #
  # Examples
  #
  #   # Hides the editor.
  #   viewer.hide()
  #
  #   # Hide the viewer on click (prevents default action).
  #   $('a.hide-viewer').bind('click', viewer.hide)
  #
  # Returns itself.
  hide: (event) =>
    Annotator.Util.preventEventDefault event

    @element.addClass(@classes.hide)
    this.publish('hide')

  # Public: Loads annotations into the viewer and shows it. Fires the "load"
  # event once the viewer is loaded passing the annotations into the callback.
  #
  # annotation - An Array of annotation elements.
  #
  # Examples
  #
  #   viewer.load([annotation1, annotation2, annotation3])
  #
  # Returns itslef.
  load: (annotations) =>
    @annotations = annotations || []

    list = @element.find('ul:first').empty()
    for annotation in @annotations
      item = $(@item).clone().appendTo(list).data('annotation', annotation)
      controls = item.find('.annotator-controls')

      link = controls.find('.annotator-link')
      edit = controls.find('.annotator-edit')
      del  = controls.find('.annotator-delete')

      links = new LinkParser(annotation.links or []).get('alternate', {'type': 'text/html'})
      if links.length is 0 or not links[0].href?
        link.remove()
      else
        link.attr('href', links[0].href)

      if @options.readOnly
        edit.remove()
        del.remove()
      else
        controller = {
          showEdit: -> edit.removeAttr('disabled')
          hideEdit: -> edit.attr('disabled', 'disabled')
          showDelete: -> del.removeAttr('disabled')
          hideDelete: -> del.attr('disabled', 'disabled')
        }

      for field in @fields
        element = $(field.element).clone().appendTo(item)[0]
        field.load(element, annotation, controller)

    this.publish('load', [@annotations])

    this.show()

  # Public: Adds an addional field to an annotation view. A callback can be
  # provided to update the view on load.
  #
  # options - An options Object. Options are as follows:
  #           load - Callback Function called when the view is loaded with an
  #                  annotation. Recieves a newly created clone of @item and
  #                  the annotation to be displayed (it will be called once
  #                  for each annotation being loaded).
  #
  # Examples
  #
  #   # Display a user name.
  #   viewer.addField({
  #     # This is called when the viewer is loaded.
  #     load: (field, annotation) ->
  #       field = $(field)
  #
  #       if annotation.user
  #         field.text(annotation.user) # Display the user
  #       else
  #         field.remove()              # Do not display the field.
  #   })
  #
  # Returns itself.
  addField: (options) ->
    field = $.extend({
      load: ->
    }, options)

    field.element = $('<div />')[0]
    @fields.push field
    field.element
    this

  # Callback function: called when the edit button is clicked.
  #
  # event - An Event object.
  #
  # Returns nothing.
  onEditClick: (event) =>
    this.onButtonClick(event, 'edit')

  # Callback function: called when the delete button is clicked.
  #
  # event - An Event object.
  #
  # Returns nothing.
  onDeleteClick: (event) =>
    this.onButtonClick(event, 'delete')

  # Fires an event of type and passes in the associated annotation.
  #
  # event - An Event object.
  # type  - The type of event to fire. Either "edit" or "delete".
  #
  # Returns nothing.
  onButtonClick: (event, type) ->
    item = $(event.target).parents('.annotator-annotation')

    this.publish(type, [item.data('annotation')])

# Private: simple parser for hypermedia link structure
#
# Examples:
#
#   links = [
#     { rel: 'alternate', href: 'http://example.com/pages/14.json', type: 'application/json' },
#     { rel: 'prev': href: 'http://example.com/pages/13' }
#   ]
#
#   lp = LinkParser(links)
#   lp.get('alternate')                      # => [ { rel: 'alternate', href: 'http://...', ... } ]
#   lp.get('alternate', {type: 'text/html'}) # => []
#
class LinkParser
  constructor: (@data) ->

  get: (rel, cond={}) ->
    cond = $.extend({}, cond, {rel: rel})
    keys = (k for own k, v of cond)
    for d in @data
      match = keys.reduce ((m, k) -> m and (d[k] is cond[k])), true
      if match
        d
      else
        continue
