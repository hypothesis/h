class Annotator.Plugin.Discovery extends Annotator.Plugin
  pluginInit: ->
    console.log "Initializing discovery plugin."

    svc = $('link')
    .filter ->
      this.rel is 'service' and this.type is 'application/annotatorsvc+json'
    .filter ->
      this.href

    return unless svc.length

    href = svc[0].href
    
    $.getJSON href, (data) =>
      return unless data?.links?

      options =
        prefix: href.replace /\/$/, ''
        urls: {}

      if data.links.search?.url?
        options.urls.search = data.links.search.url

      for action, info of (data.links.annotation or {}) when info.url?
        options.urls[action] = info.url

      for action, url of options.urls
        options.urls[action] = url.replace(options.prefix, '')

      @annotator.publish 'serviceDiscovery', options
