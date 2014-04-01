class Annotator.Plugin.Document extends Annotator.Plugin

  $ = Annotator.$
  
  events:
    'beforeAnnotationCreated': 'beforeAnnotationCreated'

  pluginInit: ->
    this.getDocumentMetadata()

  # returns the primary URI for the document being annotated
  
  uri: =>
    uri = decodeURIComponent document.location.href
    for link in @metadata
      if link.rel == "canonical"
        uri = link.href
    return uri

  # returns all uris for the document being annotated

  uris: =>
    uniqueUrls = {}
    for link in @metadata.link
      uniqueUrls[link.href] = true if link.href
    return (href for href of uniqueUrls)

  beforeAnnotationCreated: (annotation) =>
    annotation.document = @metadata

  getDocumentMetadata: =>
    @metadata = {}

    # first look for some common metadata types
    # TODO: look for microdata/rdfa?
    this._getHighwire()
    this._getDublinCore()
    this._getFacebook()
    this._getEprints()
    this._getPrism()
    this._getTwitter()
    this._getFavicon()
    this._getDocOwners()

    # extract out/normalize some things
    this._getTitle()
    this._getLinks()

    return @metadata

  _getHighwire: =>
    return @metadata.highwire = this._getMetaTags("citation", "name", "_")

  _getFacebook: =>
    return @metadata.facebook = this._getMetaTags("og", "property", ":")

  _getTwitter: =>
    return @metadata.twitter = this._getMetaTags("twitter", "name", ":")

  _getDublinCore: =>
    return @metadata.dc = this._getMetaTags("dc", "name", ".")

  _getPrism: =>
    return @metadata.prism = this._getMetaTags("prism", "name", ".")

  _getEprints: =>
    return @metadata.eprints = this._getMetaTags("eprints", "name", ".")

  _getMetaTags: (prefix, attribute, delimiter) =>
    tags = {}
    for meta in $("meta")
      name = $(meta).attr(attribute)
      content = $(meta).prop("content")
      if name
        match = name.match(RegExp("^#{prefix}#{delimiter}(.+)$", "i"))
        if match
          n = match[1]
          if tags[n]
            tags[n].push(content)
          else
            tags[n] = [content]
    return tags

  _getTitle: =>
    if @metadata.highwire.title
      @metadata.title = @metadata.highwire.title[0]
    else if @metadata.eprints.title
      @metadata.title = @metadata.eprints.title
    else if @metadata.prism.title
      @metadata.title = @metadata.prism.title
    else if @metadata.facebook.title
      @metadata.title = @metadata.facebook.title
    else if @metadata.twitter.title
      @metadata.title = @metadata.twitter.title
    else if @metadata.dc.title
      @metadata.title = @metadata.dc.title
    else
      @metadata.title = $("head title").text()
 
  _getLinks: =>
    # we know our current location is a link for the document
    @metadata.link = [href: document.location.href]

    # look for some relevant link relations
    for link in $("link")
      l = $(link)
      href = this._absoluteUrl(l.prop('href')) # get absolute url
      rel = l.prop('rel')
      type = l.prop('type')
      if rel in ["alternate", "canonical", "bookmark"] and type not in ["application/rss+xml", "application/atom+xml"]
        @metadata.link.push(href: href, rel: rel, type: type)

    # look for links in scholar metadata
    for name, values of @metadata.highwire

      if name == "pdf_url"
        for url in values
          @metadata.link.push
            href: this._absoluteUrl(url)
            type: "application/pdf"

      # kind of a hack to express DOI identifiers as links but it's a 
      # convenient place to look them up later, and somewhat sane since 
      # they don't have a type
    
      if name == "doi"
        for doi in values
          if doi[0..3] != "doi:"
            doi = "doi:" + doi
          @metadata.link.push(href: doi)

    # look for links in dublincore data
    for name, values of @metadata.dc
      if name == "identifier"
        for id in values
          if id[0..3] == "doi:"
            @metadata.link.push(href: id)

  _getFavicon: =>
    for link in $("link")
      if $(link).prop("rel") in ["shortcut icon", "icon"]
        @metadata["favicon"] = this._absoluteUrl(link.href)

  _getDocOwners: =>
    @metadata.reply_to = []

    for a in $("a")
      if a.rel is 'reply-to'
        if a.href.toLowerCase().slice(0,7) is "mailto:"
          @metadata.reply_to.push a.href[7..]
        else
          @metadata.reply_to.push a.href

  # hack to get a absolute url from a possibly relative one
  _absoluteUrl: (url) ->
    d = document.createElement('a')
    d.href = url
    d.href
