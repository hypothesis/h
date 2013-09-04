# Public: Plugin for setting permissions on newly created annotations as well as
# managing user permissions such as viewing/editing/deleting annotions.
#
# element - A DOM Element upon which events are bound. When initialised by
#           the Annotator it is the Annotator element.
# options - An Object literal containing custom options.
#
# Examples
#
#   new Annotator.plugin.Permissions(annotator.element, {
#     user: 'Alice'
#   })
#
# Returns a new instance of the Permissions Object.
class Annotator.Plugin.Permissions extends Annotator.Plugin

  # A Object literal consisting of event/method pairs to be bound to
  # @element. See Delegator#addEvents() for details.
  events:
    'beforeAnnotationCreated': 'addFieldsToAnnotation'

  # A Object literal of default options for the class.
  options:

    # Displays an "Anyone can view this annotation" checkbox in the Editor.
    showViewPermissionsCheckbox: true

    # Displays an "Anyone can edit this annotation" checkbox in the Editor.
    showEditPermissionsCheckbox: true

    # Public: Used by the plugin to determine a unique id for the @user property.
    # By default this accepts and returns the user String but can be over-
    # ridden in the @options object passed into the constructor.
    #
    # user - A String username or null if no user is set.
    #
    # Returns the String provided as user object.
    userId: (user) -> user

    # Public: Used by the plugin to determine a display name for the @user
    # property. By default this accepts and returns the user String but can be
    # over-ridden in the @options object passed into the constructor.
    #
    # user - A String username or null if no user is set.
    #
    # Returns the String provided as user object
    userString: (user) -> user

    # Public: Used by Permissions#authorize to determine whether a user can
    # perform an action on an annotation. Overriding this function allows
    # a far more complex permissions sysyem.
    #
    # By default this authorizes the action if any of three scenarios are true:
    #
    #     1) the annotation has a 'permissions' object, and either the field for
    #        the specified action is missing, empty, or contains the userId of the
    #        current user, i.e. @options.userId(@user)
    #
    #     2) the annotation has a 'user' property, and @options.userId(@user) matches
    #        'annotation.user'
    #
    #     3) the annotation has no 'permissions' or 'user' properties
    #
    # annotation - The annotation on which the action is being requested.
    # action - The action being requested: e.g. 'update', 'delete'.
    # user - The user object (or string) requesting the action. This is usually
    #        automatically passed by Permissions#authorize as the current user (@user)
    #
    #   permissions.setUser(null)
    #   permissions.authorize('update', {})
    #   # => true
    #
    #   permissions.setUser('alice')
    #   permissions.authorize('update', {user: 'alice'})
    #   # => true
    #   permissions.authorize('update', {user: 'bob'})
    #   # => false
    #
    #   permissions.setUser('alice')
    #   permissions.authorize('update', {
    #     user: 'bob',
    #     permissions: ['update': ['alice', 'bob']]
    #   })
    #   # => true
    #   permissions.authorize('destroy', {
    #     user: 'bob',
    #     permissions: [
    #       'update': ['alice', 'bob']
    #       'destroy': ['bob']
    #     ]
    #   })
    #   # => false
    #
    # Returns a Boolean, true if the user is authorised for the token provided.
    userAuthorize: (action, annotation, user) ->
      # Fine-grained custom authorization
      if annotation.permissions
        tokens = annotation.permissions[action] || []

        if tokens.length == 0
          # Empty or missing tokens array: anyone can perform action.
          return true

        for token in tokens
          if this.userId(user) == token
            return true

        # No tokens matched: action should not be performed.
        return false

      # Coarse-grained authorization
      else if annotation.user
        if user
          return this.userId(user) == this.userId(annotation.user)
        else
          return false

      # No authorization info on annotation: free-for-all!
      true

    # Default user object.
    user: ''

    # Default permissions for all annotations. Anyone can do anything
    # (assuming default userAuthorize function).
    permissions: {
      'read':   []
      'update': []
      'delete': []
      'admin':  []
    }

  # The constructor called when a new instance of the Permissions
  # plugin is created. See class documentation for usage.
  #
  # element - A DOM Element upon which events are bound..
  # options - An Object literal containing custom options.
  #
  # Returns an instance of the Permissions object.
  constructor: (element, options) ->
    super

    if @options.user
      this.setUser(@options.user)
      delete @options.user

  # Public: Initializes the plugin and registers fields with the
  # Annotator.Editor and Annotator.Viewer.
  #
  # Returns nothing.
  pluginInit: ->
    return unless Annotator.supported()

    self = this
    createCallback = (method, type) ->
      (field, annotation) -> self[method].call(self, type, field, annotation)

    # Set up user and default permissions from auth token if none currently given
    if !@user and @annotator.plugins.Auth
      @annotator.plugins.Auth.withToken(this._setAuthFromToken)

    if @options.showViewPermissionsCheckbox == true
      @annotator.editor.addField({
        type:   'checkbox'
        label:  Annotator._t('Allow anyone to <strong>view</strong> this annotation')
        load:   createCallback('updatePermissionsField', 'read')
        submit: createCallback('updateAnnotationPermissions', 'read')
      })

    if @options.showEditPermissionsCheckbox == true
      @annotator.editor.addField({
        type:   'checkbox'
        label:  Annotator._t('Allow anyone to <strong>edit</strong> this annotation')
        load:   createCallback('updatePermissionsField', 'update')
        submit: createCallback('updateAnnotationPermissions', 'update')
      })

    # Setup the display of annotations in the Viewer.
    @annotator.viewer.addField({
      load: this.updateViewer
    })

    # Add a filter to the Filter plugin if loaded.
    if @annotator.plugins.Filter
      @annotator.plugins.Filter.addFilter({
        label: Annotator._t('User')
        property: 'user'
        isFiltered: (input, user) =>
          user = @options.userString(user)

          return false unless input and user
          for keyword in (input.split /\s*/)
            return false if user.indexOf(keyword) == -1

          return true
      })

  # Public: Sets the Permissions#user property.
  #
  # user - A String or Object to represent the current user.
  #
  # Examples
  #
  #   permissions.setUser('Alice')
  #
  #   permissions.setUser({id: 35, name: 'Alice'})
  #
  # Returns nothing.
  setUser: (user) ->
    @user = user

  # Event callback: Appends the @user and @options.permissions objects to the
  # provided annotation object. Only appends the user if one has been set.
  #
  # annotation - An annotation object.
  #
  # Examples
  #
  #   annotation = {text: 'My comment'}
  #   permissions.addFieldsToAnnotation(annotation)
  #   console.log(annotation)
  #   # => {text: 'My comment', permissions: {...}}
  #
  # Returns nothing.
  addFieldsToAnnotation: (annotation) =>
    if annotation
      annotation.permissions = @options.permissions
      if @user
        annotation.user = @user

  # Public: Determines whether the provided action can be performed on the
  # annotation. This uses the user-configurable 'userAuthorize' method to
  # determine if an annotation is annotatable. See the default method for
  # documentation on its behaviour.
  #
  # Returns a Boolean, true if the action can be performed on the annotation.
  authorize: (action, annotation, user) ->
    user = @user if user == undefined

    if @options.userAuthorize
      return @options.userAuthorize.call(@options, action, annotation, user)

    else # userAuthorize nulled out: free-for-all!
      return true

  # Field callback: Updates the state of the "anyone can…" checkboxes
  #
  # action     - The action String, either "view" or "update"
  # field      - A DOM Element containing a form input.
  # annotation - An annotation Object.
  #
  # Returns nothing.
  updatePermissionsField: (action, field, annotation) =>
    field = $(field).show()
    input = field.find('input').removeAttr('disabled')

    # Do not show field if current user is not admin.
    field.hide() unless this.authorize('admin', annotation)

    # See if we can authorise without a user.
    if this.authorize(action, annotation || {}, null)
      input.attr('checked', 'checked')
    else
      input.removeAttr('checked')


  # Field callback: updates the annotation.permissions object based on the state
  # of the field checkbox. If it is checked then permissions are set to world
  # writable otherwise they use the original settings.
  #
  # action     - The action String, either "view" or "update"
  # field      - A DOM Element representing the annotation editor.
  # annotation - An annotation Object.
  #
  # Returns nothing.
  updateAnnotationPermissions: (type, field, annotation) =>
    annotation.permissions = @options.permissions unless annotation.permissions

    dataKey = type + '-permissions'

    if $(field).find('input').is(':checked')
      annotation.permissions[type] = []
    else
      # Clearly, the permissions model allows for more complex entries than this,
      # but our UI presents a checkbox, so we can only interpret "prevent others
      # from viewing" as meaning "allow only me to view". This may want changing
      # in the future.
      annotation.permissions[type] = [@user]

  # Field callback: updates the annotation viewer to inlude the display name
  # for the user obtained through Permissions#options.userString().
  #
  # field      - A DIV Element representing the annotation field.
  # annotation - An annotation Object to display.
  # controls   - A control Object to toggle the display of annotation controls.
  #
  # Returns nothing.
  updateViewer: (field, annotation, controls) =>
    field = $(field)

    username = @options.userString annotation.user
    if annotation.user and username and typeof username == 'string'
      user = Annotator.Util.escape(@options.userString(annotation.user))
      field.html(user).addClass('annotator-user')
    else
      field.remove()

    if controls
      controls.hideEdit()   unless this.authorize('update', annotation)
      controls.hideDelete() unless this.authorize('delete', annotation)

  # Sets the Permissions#user property on the basis of a received authToken.
  #
  # token - the authToken received by the Auth plugin
  #
  # Returns nothing.
  _setAuthFromToken: (token) =>
    this.setUser(token.userId)

