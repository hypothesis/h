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
    # Create a sidebar if one does not exist. This is a singleton element
    # even if multiple instances of the app are loaded on a page (some day).
    @sidebar = $('#hypothesis-sidebar').get(0)
    if not @sidebar?
      @sidebar = $("<div class='annotator-wrapper' id='hypothesis-sidebar'></div>")
    super

    # Load plugins
    $.extend @pluginConfig, options
    for own name, opts of @pluginConfig
      if not @plugins[name]
        this.addPlugin name, opts

    # Pull the viewer and editor into the sidebar, instead of the wrapper
    @viewer.element.detach().appendTo(@sidebar)
    @editor.element.detach().appendTo(@sidebar)

    # Pull the heatmap into the sidebar
    @heatmap = @plugins.Heatmap
    @heatmap.element.prependTo(@sidebar)

    # Drop the sidebar into the beginning of the wrapper (so it can be floated)
    @sidebar.prependTo(@wrapper)

    this

  onHeatmapClick: (event) =>
    target = d3.bisect(@heatmap.index, event.offsetY)-1
    annotations = @heatmap.buckets[target]

    if annotations?.length
      this.showViewer(annotations, {})
    else
      this.viewer.hide(event)

    @heatmap.updateHeatmap()
