class Hypothesis extends Annotator
  events:
    ".annotator-adder button click":     "onAdderClick"
    ".annotator-adder button mousedown": "onAdderMousedown"
    ".annotator-heatmap click":          "onHeatmapClick"

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

  onHeatmapClick: (event) =>
    y = event.pageY - @wrapper.offset().top
    target = d3.bisect(@heatmap.index, y)-1
    annotations = @heatmap.buckets[target]

    this.showViewer(annotations)
    @heatmap.updateHeatmap()

  showViewer: (annotations) ->
    @viewer.element.find('.annotator-listing').replaceWith(
      Handlebars.templates['summaries']({
        annotations: annotations
      })
    )
    @viewer.show()
    $(document.documentElement).addClass('hyp-collapse')
    @sidebar.removeClass('collapse')

  showEditor: (annotation) =>
    if @plugins.Permissions?.user
      annotation['user'] = @plugins.Permissions.user
      @editor.element.find('.annotator-listing').replaceWith(
        Handlebars.templates['editor'](annotation)
      )
      @editor.load(annotation)
      $(document.documentElement).addClass('hyp-collapse')
      @sidebar.removeClass('collapse')
    else
      alert("Not logged in!")

  # Sets up the selection event listeners to watch mouse actions on the document.
  #
  # Returns itself for chaining.
  _setupDocumentEvents: ->
    super
    $(document).on('mousedown', () =>
      @sidebar.addClass('collapse')
      $(document.documentElement).removeClass('hyp-collapse')
      setTimeout((() -> $(window).resize()), 600)
    )
    this

  _setupHeatmap: () ->
    # Pull the heatmap into the sidebar
    @heatmap = @plugins.Heatmap
    this

  _setupSidebar: () ->
    # Create a sidebar if one does not exist. This is a singleton element --
    # even if multiple instances of the app are loaded on a page (some day).
    if not @sidebar?
      sidebar = $(Handlebars.templates['sidebar']())
      Annotator.prototype.sidebar = sidebar
      @sidebar = sidebar
      @sidebar.addClass('collapse')

      # Capture mouse down so as not to close to sidebar.
      @sidebar.on('mousedown', (event) =>
        event.stopImmediatePropagation()
      )
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
      .addField({
        load: (field, annotation) =>
          if annotation.text
            $(field).escape(annotation.text)
          else
            $(field).html("<i>#{_t 'No Comment'}</i>")
          this.publish('annotationViewerTextField', [field, annotation])
      })
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
    .addField({
      type: 'textarea',
      label: _t('Comments') + '\u2026'
      load: (field, annotation) ->
        $(field).find('textarea').val(annotation.text || '')
      submit: (field, annotation) ->
        annotation.text = $(field).find('textarea').val()
      })
    this