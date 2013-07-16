# Public: A initialization function that sets up the Annotator and some of the
# default plugins. Intended for use with the annotator-full package.
#
# NOTE: This method is intened to be called via the jQuery .annotator() method
# although it is available directly on the Annotator instance.
#
# config  - An object containing config options for the AnnotateIt store.
#             storeUrl: API endpoint for the store (default: "http://annotateit.org/api")
#             tokenUrl: API endpoint for auth token provider (default: "http://annotateit.org/api/token")
#
# options - An object containing plugin settings to override the defaults.
#           If a plugin is entered with a 'falsy' value, the plugin will not be loaded.
#
# Examples
#
#   $('#content').annotator().annotator('setupPlugins');
#
#   // Only display a filter for the user field and disable tags.
#   $('#content').annotator().annotator('setupPlugins', null, {
#     Tags: false,
#     Filter: {
#       filters: [{label: 'User', property: 'user'}],
#       addAnnotationFilter: false
#     }
#   });
#
# Returns itself for chaining.
Annotator::setupPlugins = (config={}, options={}) ->
  win = Annotator.Util.getGlobal()

  # Set up the default plugins.
  plugins = ['Unsupported', 'Auth', 'Tags', 'Filter', 'Store', 'AnnotateItPermissions']

  # If Showdown is included add the Markdown plugin.
  if win.Showdown
    plugins.push('Markdown')

  # Check the config for store credentials and add relevant plugins.
  uri = win.location.href.split(/#|\?/).shift() or ''

  pluginConfig =
    Tags: {}
    Filter:
      filters: [
        {label: Annotator._t('User'), property: 'user'}
        {label: Annotator._t('Tags'), property: 'tags'}
      ]
    Auth:
      tokenUrl: config.tokenUrl or 'http://annotateit.org/api/token'
    Store:
      prefix: config.storeUrl or 'http://annotateit.org/api'
      annotationData:
        uri: uri
      loadFromSearch:
        uri: uri

  for own name, opts of options
    if name not in plugins
      plugins.push(name)

  $.extend true, pluginConfig, options

  for name in plugins
    if name not of pluginConfig or pluginConfig[name]
      this.addPlugin(name, pluginConfig[name])
