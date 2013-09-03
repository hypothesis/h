# Public: The Store plugin can be used to persist annotations to a database
# running on your server. It has a simple customisable interface that can be
# implemented with any web framework. It works by listening to events published
# by the Annotator and making appropriate requests to the server depending on
# the event.
#
# The store handles five distinct actions "read", "search", "create", "update"
# and "destory". The requests made can be customised with options when the
# plugin is added to the Annotator. Custom headers can also be sent with every
# request by setting a $.data key on the Annotation#element containing headers
# to send. e.g:
#
#   annotator.element.data('annotation:headers', {
#     'X-My-Custom-Header': 'MyCustomValue'
#   })
#
# This header will now be sent with every request.
class Annotator.Plugin.Store extends Annotator.Plugin
  # The store listens for the following events published by the Annotator.
  # - annotationCreated: A new annotation has been created.
  # - annotationUpdated: An annotation has been updated.
  # - annotationDeleted: An annotation has been deleted.
  events:
    'annotationCreated': 'annotationCreated'
    'annotationDeleted': 'annotationDeleted'
    'annotationUpdated': 'annotationUpdated'

  # User customisable options available.
  options:

    # Custom meta data that will be attached to every annotation that is sent
    # to the server. This _will_ override previous values.
    annotationData: {}

    # Should the plugin emulate HTTP methods like PUT and DELETE for
    # interaction with legacy web servers? Setting this to `true` will fake
    # HTTP `PUT` and `DELETE` requests with an HTTP `POST`, and will set the
    # request header `X-HTTP-Method-Override` with the name of the desired
    # method.
    emulateHTTP: false

    # If loadFromSearch is set, then we load the first batch of
    # annotations from the 'search' URL as set in `options.urls`
    # instead of the registry path 'prefix/read'.
    #
    #     loadFromSearch: {
    #       'limit': 0,
    #       'all_fields': 1
    #       'uri': 'http://this/document/only'
    #     }
    loadFromSearch: false

    # This is the API endpoint. If the server supports Cross Origin Resource
    # Sharing (CORS) a full URL can be used here.
    prefix: '/store'

    # The server URLs for each available action. These URLs can be anything but
    # must respond to the appropraite HTTP method. The token ":id" can be used
    # anywhere in the URL and will be replaced with the annotation id.
    #
    # read:    GET
    # create:  POST
    # update:  PUT
    # destroy: DELETE
    # search:  GET
    urls:
      create:  '/annotations'
      read:    '/annotations/:id'
      update:  '/annotations/:id'
      destroy: '/annotations/:id'
      search:  '/search'

  # Public: The contsructor initailases the Store instance. It requires the
  # Annotator#element and an Object of options.
  #
  # element - This must be the Annotator#element in order to listen for events.
  # options - An Object of key/value user options.
  #
  # Examples
  #
  #   store = new Annotator.Plugin.Store(Annotator.element, {
  #     prefix: 'http://annotateit.org',
  #     annotationData: {
  #       uri: window.location.href
  #     }
  #   })
  #
  # Returns a new instance of Store.
  constructor: (element, options) ->
    super
    @annotations = []

  # Public: Initialises the plugin and loads the latest annotations. If the
  # Auth plugin is also present it will request an auth token before loading
  # any annotations.
  #
  # Examples
  #
  #   store.pluginInit()
  #
  # Returns nothing.
  pluginInit: ->
    return unless Annotator.supported()

    if @annotator.plugins.Auth
      @annotator.plugins.Auth.withToken(this._getAnnotations)
    else
      this._getAnnotations()

  # Checks the loadFromSearch option and if present loads annotations using
  # the Store#loadAnnotationsFromSearch method rather than Store#loadAnnotations.
  #
  # Returns nothing.
  _getAnnotations: =>
    if @options.loadFromSearch
      this.loadAnnotationsFromSearch(@options.loadFromSearch)
    else
      this.loadAnnotations()

  # Public: Callback method for annotationCreated event. Receives an annotation
  # and sends a POST request to the sever using the URI for the "create" action.
  #
  # annotation - An annotation Object that was created.
  #
  # Examples
  #
  #   store.annotationCreated({text: "my new annotation comment"})
  #   # => Results in an HTTP POST request to the server containing the
  #   #    annotation as serialised JSON.
  #
  # Returns nothing.
  annotationCreated: (annotation) ->
    # Pre-register the annotation so as to save the list of highlight
    # elements.
    if annotation not in @annotations
      this.registerAnnotation(annotation)

      this._apiRequest('create', annotation, (data) =>
        # Update with (e.g.) ID from server.
        if not data.id?
          console.warn Annotator._t("Warning: No ID returned from server for annotation "), annotation
        this.updateAnnotation annotation, data
      )
    else
      # This is called to update annotations created at load time with
      # the highlight elements created by Annotator.
      this.updateAnnotation annotation, {}

  # Public: Callback method for annotationUpdated event. Receives an annotation
  # and sends a PUT request to the sever using the URI for the "update" action.
  #
  # annotation - An annotation Object that was updated.
  #
  # Examples
  #
  #   store.annotationUpdated({id: "blah", text: "updated annotation comment"})
  #   # => Results in an HTTP PUT request to the server containing the
  #   #    annotation as serialised JSON.
  #
  # Returns nothing.
  annotationUpdated: (annotation) ->
    if annotation in this.annotations
      this._apiRequest 'update', annotation, ((data) => this.updateAnnotation(annotation, data))

  # Public: Callback method for annotationDeleted event. Receives an annotation
  # and sends a DELETE request to the server using the URI for the destroy
  # action.
  #
  # annotation - An annotation Object that was deleted.
  #
  # Examples
  #
  #   store.annotationDeleted({text: "my new annotation comment"})
  #   # => Results in an HTTP DELETE request to the server.
  #
  # Returns nothing.
  annotationDeleted: (annotation) ->
    if annotation in this.annotations
      this._apiRequest 'destroy', annotation, (() => this.unregisterAnnotation(annotation))

  # Public: Registers an annotation with the Store. Used to check whether an
  # annotation has already been created when using Store#annotationCreated().
  #
  # NB: registerAnnotation and unregisterAnnotation do no error-checking/
  # duplication avoidance of their own. Use with care.
  #
  # annotation - An annotation Object to resister.
  #
  # Examples
  #
  #   store.registerAnnotation({id: "annotation"})
  #
  # Returns registed annotations.
  registerAnnotation: (annotation) ->
    @annotations.push(annotation)

  # Public: Unregisters an annotation with the Store.
  #
  # NB: registerAnnotation and unregisterAnnotation do no error-checking/
  # duplication avoidance of their own. Use with care.
  #
  # annotation - An annotation Object to unresister.
  #
  # Examples
  #
  #   store.unregisterAnnotation({id: "annotation"})
  #
  # Returns remaining registed annotations.
  unregisterAnnotation: (annotation) ->
    @annotations.splice(@annotations.indexOf(annotation), 1)

  # Public: Extends the provided annotation with the contents of the data
  # Object. Will only extend annotations that have been registered with the
  # store. Also updates the annotation object stored in the 'annotation' data
  # store.
  #
  # annotation - An annotation Object to extend.
  # data       - An Object containing properties to add to the annotation.
  #
  # Examples
  #
  #   annotation = $('.annotation-hl:first').data('annotation')
  #   store.updateAnnotation(annotation, {extraProperty: "bacon sarnie"})
  #   console.log($('.annotation-hl:first').data('annotation').extraProperty)
  #   # => Outputs "bacon sarnie"
  #
  # Returns nothing.
  updateAnnotation: (annotation, data) ->
    if annotation not in this.annotations
      console.error Annotator._t("Trying to update unregistered annotation!")
    else
      $.extend(annotation, data)

    # Update the elements with our copies of the annotation objects (e.g.
    # with ids from the server).
    $(annotation.highlights).data('annotation', annotation)

  # Public: Makes a request to the server for all annotations.
  #
  # Examples
  #
  #   store.loadAnnotations()
  #
  # Returns nothing.
  loadAnnotations: () ->
    this._apiRequest 'read', null, this._onLoadAnnotations

  # Callback method for Store#loadAnnotations(). Processes the data
  # returned from the server (a JSON array of annotation Objects) and updates
  # the registry as well as loading them into the Annotator.
  #
  # data - An Array of annotation Objects
  #
  # Examples
  #
  #   console.log @annotation # => []
  #   store._onLoadAnnotations([{}, {}, {}])
  #   console.log @annotation # => [{}, {}, {}]
  #
  # Returns nothing.
  _onLoadAnnotations: (data=[]) =>

    annotationMap = {}
    for a in @annotations
      annotationMap[a.id] = a

    newData = []
    for a in data
      if annotationMap[a.id]
        annotation = annotationMap[a.id]
        this.updateAnnotation annotation, a
      else
        newData.push(a)

    @annotations = @annotations.concat(newData)
    @annotator.loadAnnotations(newData.slice()) # Clone array

  # Public: Performs the same task as Store.#loadAnnotations() but calls the
  # 'search' URI with an optional query string.
  #
  # searchOptions - Object literal of query string parameters.
  #
  # Examples
  #
  #   store.loadAnnotationsFromSearch({
  #     limit: 100,
  #     uri: window.location.href
  #   })
  #
  # Returns nothing.
  loadAnnotationsFromSearch: (searchOptions) ->
    this._apiRequest 'search', searchOptions, this._onLoadAnnotationsFromSearch

  # Callback method for Store#loadAnnotationsFromSearch(). Processes the data
  # returned from the server (a JSON array of annotation Objects) and updates
  # the registry as well as loading them into the Annotator.
  #
  # data - An Array of annotation Objects
  #
  # Returns nothing.
  _onLoadAnnotationsFromSearch: (data={}) =>
    this._onLoadAnnotations(data.rows || [])

  # Public: Dump an array of serialized annotations
  #
  # param - comment
  #
  # Examples
  #
  #   example
  #
  # Returns
  dumpAnnotations: ->
    (JSON.parse(this._dataFor(ann)) for ann in @annotations)

  # Callback method for Store#loadAnnotationsFromSearch(). Processes the data
  # returned from the server (a JSON array of annotation Objects) and updates
  # the registry as well as loading them into the Annotator.
  # Returns the jQuery XMLHttpRequest wrapper enabling additional callbacks to
  # be applied as well as custom error handling.
  #
  # action    - The action String eg. "read", "search", "create", "update"
  #             or "destory".
  # obj       - The data to be sent, either annotation object or query string.
  # onSuccess - A callback Function to call on successful request.
  #
  # Examples:
  #
  #   store._apiRequest('read', {id: 4}, (data) -> console.log(data))
  #   # => Outputs the annotation returned from the server.
  #
  # Returns jXMLHttpRequest object.
  _apiRequest: (action, obj, onSuccess) ->
    id  = obj && obj.id
    url = this._urlFor(action, id)
    options = this._apiRequestOptions(action, obj, onSuccess)

    request = $.ajax(url, options)

    # Append the id and action to the request object
    # for use in the error callback.
    request._id = id
    request._action = action
    request

  # Builds an options object suitable for use in a jQuery.ajax() call.
  #
  # action    - The action String eg. "read", "search", "create", "update"
  #             or "destory".
  # obj       - The data to be sent, either annotation object or query string.
  # onSuccess - A callback Function to call on successful request.
  #
  # Also extracts any custom headers from data stored on the Annotator#element
  # under the 'annotator:headers' key. These headers should be stored as key/
  # value pairs and will be sent with every request.
  #
  # Examples
  #
  #   annotator.element.data('annotator:headers', {
  #     'X-My-Custom-Header': 'CustomValue',
  #     'X-Auth-User-Id': 'bill'
  #   })
  #
  # Returns Object literal of $.ajax() options.
  _apiRequestOptions: (action, obj, onSuccess) ->
    method = this._methodFor(action)

    opts = {
      type:       method,
      headers:    @element.data('annotator:headers'),
      dataType:   "json",
      success:    (onSuccess or ->),
      error:      this._onError
    }

    # If emulateHTTP is enabled, we send a POST and put the real method in an
    # HTTP request header.
    if @options.emulateHTTP and method in ['PUT', 'DELETE']
      opts.headers = $.extend(opts.headers, {'X-HTTP-Method-Override': method})
      opts.type = 'POST'

    # Don't JSONify obj if making search request.
    if action is "search"
      opts = $.extend(opts, data: obj)
      return opts

    data = obj && this._dataFor(obj)

    # If emulateJSON is enabled, we send a form request (the correct
    # contentType will be set automatically by jQuery), and put the
    # JSON-encoded payload in the "json" key.
    if @options.emulateJSON
      opts.data = {json: data}
      if @options.emulateHTTP
        opts.data._method = method
      return opts

    opts = $.extend(opts, {
      data: data
      contentType: "application/json; charset=utf-8"
    })
    return opts

  # Builds the appropriate URL from the options for the action provided.
  #
  # action - The action String.
  # id     - The annotation id as a String or Number.
  #
  # Examples
  #
  #   store._urlFor('update', 34)
  #   # => Returns "/store/annotations/34"
  #
  #   store._urlFor('search')
  #   # => Returns "/store/search"
  #
  # Returns URL String.
  _urlFor: (action, id) ->
    url = if @options.prefix? then @options.prefix else ''
    url += @options.urls[action]
    # If there's a '/:id' in the URL, either fill in the ID or remove the
    # slash:
    url = url.replace(/\/:id/, if id? then '/' + id else '')
    # If there's a bare ':id' in the URL, then substitute directly:
    url = url.replace(/:id/, if id? then id else '')

    url

  # Maps an action to an HTTP method.
  #
  # action - The action String.
  #
  # Examples
  #
  #   store._methodFor('read')    # => "GET"
  #   store._methodFor('update')  # => "PUT"
  #   store._methodFor('destroy') # => "DELETE"
  #
  # Returns HTTP method String.
  _methodFor: (action) ->
    table = {
      'create':  'POST'
      'read':    'GET'
      'update':  'PUT'
      'destroy': 'DELETE'
      'search':  'GET'
    }

    table[action]

  # Creates a JSON serialisation of an annotation.
  #
  # annotation - An annotation Object to serialise.
  #
  # Examples
  #
  #   store._dataFor({id: 32, text: 'my annotation comment'})
  #   # => Returns '{"id": 32, "text":"my annotation comment"}'
  #
  # Returns
  _dataFor: (annotation) ->
    # Store a reference to the highlights array. We can't serialize
    # a list of HTMLElement objects.
    highlights = annotation.highlights

    delete annotation.highlights

    # Preload with extra data.
    $.extend(annotation, @options.annotationData)
    data = JSON.stringify(annotation)

    # Restore the highlights array.
    annotation.highlights = highlights if highlights

    data

  # jQuery.ajax() callback. Displays an error notification to the user if
  # the request failed.
  #
  # xhr - The jXMLHttpRequest object.
  #
  # Returns nothing.
  _onError: (xhr) =>
    action  = xhr._action
    message = Annotator._t("Sorry we could not ") + action + Annotator._t(" this annotation")

    if xhr._action == 'search'
      message = Annotator._t("Sorry we could not search the store for annotations")
    else if xhr._action == 'read' && !xhr._id
      message = Annotator._t("Sorry we could not ") + action + Annotator._t(" the annotations from the store")

    switch xhr.status
      when 401 then message = Annotator._t("Sorry you are not allowed to ") + action + Annotator._t(" this annotation")
      when 404 then message = Annotator._t("Sorry we could not connect to the annotations store")
      when 500 then message = Annotator._t("Sorry something went wrong with the annotation store")

    Annotator.showNotification message, Annotator.Notification.ERROR

    console.error Annotator._t("API request failed:") + " '#{xhr.status}'"
