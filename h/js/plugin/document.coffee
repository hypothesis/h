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
    this._getScholar()
    this._getDublinCore()
    this._getOpenGraph()
    this._getFavicon()

    # extract out/normalize some things
    this._getTitle()
    this._getLinks()

    return @metadata

  _getScholar: =>
    @metadata.scholar = {}
    for meta in $("meta")
      name = $(meta).prop("name")
      content = $(meta).prop("content")
      if name.match(/^citation_/)
        if @metadata.scholar[name]
          @metadata.scholar[name].push(content)
        else
          @metadata.scholar[name] = [content]

  _getDublinCore: =>
    @metadata.dc = {}
    for meta in $("meta")
      name = $(meta).prop("name")
      content = $(meta).prop("content")
      nameParts = name.split(".")
      if nameParts.length == 2 and nameParts[0].toLowerCase() == "dc"
        n = nameParts[1]
        if @metadata.dc[n]
          @metadata.dc[n].push(content)
        else
          @metadata.dc[n] = [content]

  _getOpenGraph: =>
    @metadata.og = {}
    for meta in $("meta")
      property = $(meta).attr("property")
      content = $(meta).prop("content")
      if property
        match = property.match(/^og:(.+)$/)
        if match
          n = match[1]
          if @metadata.og[n]
            @metadata.og[n].push(content)
          else
            @metadata.og[n] = [content]

  _getTitle: =>
    if @metadata.scholar.citation_title
      @metadata.title = @metadata.scholar.citation_title[0]
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
      if rel in ["alternate", "canonical"] and type not in ["application/rss+xml", "application/atom+xml"]
        @metadata.link.push(href: href, rel: rel, type: type)

    # look for links in scholar metadata
    for name, values of @metadata.scholar

      if name == "citation_pdf_url"
        for url in values
          @metadata.link.push
            href: this._absoluteUrl(url)
            type: "application/pdf"

      # kind of a hack to express DOI identifiers as links but it's a 
      # convenient place to look them up later, and somewhat sane since 
      # they don't have a type
    
      if name == "citation_doi"
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
        
  # hack to get a absolute url from a possibly relative one
  
  _absoluteUrl: (url) ->
    img = $("<img src='#{ url }'>")
    url = img.prop('src')
    img.prop('src', null)
    return url
