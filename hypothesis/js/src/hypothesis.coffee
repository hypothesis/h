class Hypothesis extends Annotator
  events:
    ".annotator-adder button click":     "onAdderClick"
    ".annotator-adder button mousedown": "onAdderMousedown"

  pluginConfig:
    Heatmap: {}
    Permissions:
      showEditPermissionsCheckbox: false,
      showViewPermissionsCheckbox: false,
      userString: (user) -> user.replace(/^acct:(.+)@(.+)$/, '$1 on $2')
    Store:
      loadFromSearch: document.location.href
      annotationData: document.location.href
    Unsupported: {}

  constructor: (element, options) ->
    super

    # Load plugins
    $.extend @pluginConfig, options
    for own name, opts of @pluginConfig
      if not @plugins[name]
        this.addPlugin name, opts

    # Set up interface elements
    this._setupHeatmap()._setupSidebar()

    @heatmap.element.appendTo(@sidebar)
    @viewer.element.appendTo(@sidebar)
    @editor.element.appendTo(@sidebar)
    @sidebar.prependTo(@wrapper)

    @plugins.Auth.withToken (token) =>
      @plugins.Permissions.setUser token.userId

    this

  # Sets up the selection event listeners to watch mouse actions on the document.
  #
  # Returns itself for chaining.
  _setupDocumentEvents: ->
    super
    $(document).on 'mousedown', () =>
      @sidebar.addClass('collapse')
      $(document.documentElement).removeClass('hyp-collapse')
    this

  _setupSidebar: () ->
    # Create a sidebar if one does not exist. This is a singleton element --
    # even if multiple instances of the app are loaded on a page (some day).
    if not @sidebar?
      sidebar = $(Handlebars.templates.sidebar())
      Annotator.prototype.sidebar = sidebar
      @sidebar = sidebar
      @sidebar.addClass('collapse')

      # Capture mouse down so as not to close to sidebar.
      @sidebar.on('mousedown', (event) =>
        event.stopImmediatePropagation()
      )
    this

  _setupHeatmap: () ->
    # Pull the heatmap into the sidebar
    @heatmap = @plugins.Heatmap
    d3.select(@heatmap.element.get(0)).on('click', this.onHeatmapClick)
    this

  # Creates an instance of Annotator.Viewer and assigns it to the @viewer
  # property, appends it to the @wrapper and sets up event listeners.
  #
  # Returns itself to allow chaining.
  _setupViewer: ->
    @viewer = new Annotator.Viewer(readOnly: @options.readOnly)
    @viewer.hide()
    .on("edit", this.onEditAnnotation)
    .on("delete", this.onDeleteAnnotation)
    this


  # Creates an instance of the Annotator.Editor and assigns it to @editor.
  # Appends this to the @wrapper and sets up event listeners.
  #
  # Returns itself for chaining.
  _setupEditor: ->
    @editor = new Annotator.Editor()
    @editor.hide()
    .on('hide', this.onEditorHide)
    .on('save', this.onEditorSubmit)
    @editor.fields = [{
      element: @editor.element,
      load: (field, annotation) ->
        $(field).find('textarea').val(annotation.text || '')
      submit: (field, annotation) ->
        annotation.text = $(field).find('textarea').val()
    }]
    this.subscribe('annotationEditorHidden', this.showViewer)
    this.subscribe(
      'annotationEditorSubmit',
      (editor, annotation) =>
        setTimeout(() => this.showViewer([annotation]))
    )
    this

  onHeatmapClick: () =>
    [x, y] = d3.mouse(d3.event.target)
    target = d3.bisect(@heatmap.index, y)-1
    annotations = @heatmap.buckets[target]

    this.showViewer(annotations)
    @heatmap.updateHeatmap()

  showViewer: (annotations=[], detail=false) ->
    listing = d3.select(@viewer.element.find('.annotator-listing').get(0))

    if not detail
      summaries = listing.selectAll('li').data(annotations)

      summaries.enter().append('li')
      summaries.exit().remove()
      summaries
        .classed('hyp-widget', true)
        .classed('hyp-reply', false)
        .classed('hyp-summary', true)
        .html((a, i) => Handlebars.templates.summary(a))
        .on 'click', (d, i) =>
          this.showViewer([d], true)
    else
      details = listing.selectAll('li').data(annotations)

      details.enter().append('li')
      details.exit().remove()
      details
        .classed('hyp-widget', true)
        .classed('hyp-annotation', true)
        .classed('hyp-summary', false)
        .html((a, i) => Handlebars.templates.detail(a))

      excerpt = listing.selectAll('.hyp-widget.hyp-excerpt')
        .data(annotations[0..1])

      excerpt.enter().insert('li', '.hyp-annotation')
      excerpt.exit().remove()
      excerpt
        .classed('hyp-widget', true)
        .classed('hyp-excerpt', true)
        .text((d) -> d.quote)

    @viewer.show()
    $(document.documentElement).addClass('hyp-collapse')
    @sidebar.removeClass('collapse')

  showEditor: (annotation) =>
    if @plugins.Permissions?.user
      @editor.load(annotation)
      controls = @editor.element.find('.annotator-controls')
      @editor.element.find('.annotator-listing').replaceWith(
        Handlebars.templates.editor(annotation)
      )
      controls.detach().appendTo(@editor.element.find('.hyp-meta'))
      $(document.documentElement).addClass('hyp-collapse')
      @sidebar.removeClass('collapse')
    else
      alert("Not logged in!")
