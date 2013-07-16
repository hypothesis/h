# Public: Plugin for managing user permissions under the rather more specialised
# permissions model used by [AnnotateIt](http://annotateit.org).
#
# element - A DOM Element upon which events are bound. When initialised by
#           the Annotator it is the Annotator element.
# options - An Object literal containing custom options.
#
# Examples
#
#   new Annotator.plugin.AnnotateItPermissions(annotator.element)
#
# Returns a new instance of the AnnotateItPermissions Object.
class Annotator.Plugin.AnnotateItPermissions extends Annotator.Plugin.Permissions

  # A Object literal of default options for the class.
  options:

    # Displays an "Anyone can view this annotation" checkbox in the Editor.
    showViewPermissionsCheckbox: true

    # Displays an "Anyone can edit this annotation" checkbox in the Editor.
    showEditPermissionsCheckbox: true

    # Abstract user groups used by userAuthorize function
    groups:
      world: 'group:__world__'
      authenticated: 'group:__authenticated__'
      consumer: 'group:__consumer__'

    userId: (user) -> user.userId
    userString: (user) -> user.userId

    # Public: Used by AnnotateItPermissions#authorize to determine whether a user can
    # perform an action on an annotation.
    #
    # This should do more-or-less the same thing as the server-side authorization
    # code, which is to be found at
    #   https://github.com/okfn/annotator-store/blob/master/annotator/authz.py
    #
    # Returns a Boolean, true if the user is authorised for the action provided.
    userAuthorize: (action, annotation, user) ->
      permissions = annotation.permissions or {}
      action_field = permissions[action] or []

      if @groups.world in action_field
        return true

      else if user? and user.userId? and user.consumerKey?
        if user.userId == annotation.user and user.consumerKey == annotation.consumer
          return true
        else if @groups.authenticated in action_field
          return true
        else if user.consumerKey == annotation.consumer and @groups.consumer in action_field
          return true
        else if user.consumerKey == annotation.consumer and user.userId in action_field
          return true
        else if user.consumerKey == annotation.consumer and user.admin
          return true
        else
          return false
      else
        return false

    # Default permissions for all annotations. Anyone can
    # read, but only annotation owners can update/delete/admin.
    permissions: {
      'read':   ['group:__world__']
      'update': []
      'delete': []
      'admin':  []
    }

  # Event callback: Appends the @options.permissions, @options.user and
  # @options.consumer objects to the provided annotation object.
  #
  # annotation - An annotation object.
  #
  # Examples
  #
  #   annotation = {text: 'My comment'}
  #   permissions.addFieldsToAnnotation(annotation)
  #   console.log(annotation)
  #   # => {text: 'My comment', user: 'alice', consumer: 'annotateit', permissions: {...}}
  #
  # Returns nothing.
  addFieldsToAnnotation: (annotation) =>
    if annotation
      annotation.permissions = @options.permissions
      if @user
        annotation.user = @user.userId
        annotation.consumer = @user.consumerKey

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

    # See if we can authorise with any old user from this consumer
    if @user and this.authorize(action, annotation || {}, {userId: '__nonexistentuser__', consumerKey: @user.consumerKey})
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
      annotation.permissions[type] = [if type == 'read' then @options.groups.world else @options.groups.consumer]
    else
      annotation.permissions[type] = []

  # Sets the Permissions#user property on the basis of a received authToken. This plugin
  # simply uses the entire token to represent the user.
  #
  # token - the authToken received by the Auth plugin
  #
  # Returns nothing.
  _setAuthFromToken: (token) =>
    this.setUser(token)
