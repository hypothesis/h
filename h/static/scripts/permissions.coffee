###*
# @ngdoc service
# @name  Permissions
#
# @description
# This service can set default permissions to annotations properly and
# offers some utility functions regarding those.
###
module.exports = ['session', (session) ->
  ALL_PERMISSIONS = {}
  GROUP_WORLD = 'group:__world__'
  ADMIN_PARTY = [{
    allow: true
    principal: GROUP_WORLD
    action: ALL_PERMISSIONS
  }]

  # Creates access control list from context.permissions
  _acl = (context) ->
    parts =
      for action, roles of context.permissions or []
        for role in roles
          allow: true
          principal: role
          action: action

    if parts.length
      Array::concat parts...
    else
      ADMIN_PARTY

  ###*
  # @ngdoc method
  # @name permissions#private
  #
  # Sets permissions for a private annotation
  # Typical use: annotation.permissions = permissions.private()
  ###
  private: ->
    read: [session.state.userid]
    update: [session.state.userid]
    delete: [session.state.userid]
    admin: [session.state.userid]

  ###*
  # @ngdoc method
  # @name permissions#private
  #
  # Sets permissions for a public annotation
  # Typical use: annotation.permissions = permissions.public()
  ###
  public: ->
    read: [GROUP_WORLD]
    update: [session.state.userid]
    delete: [session.state.userid]
    admin: [session.state.userid]

  ###*
  # @ngdoc method
  # @name permissions#isPublic
  #
  # @param {Object} permissions
  #
  # This function determines whether the permissions allow public visibility
  ###
  isPublic: (permissions) ->
    GROUP_WORLD in (permissions?.read or [])

  ###*
  # @ngdoc method
  # @name permissions#isPrivate
  #
  # @param {Object} permissions
  # @param {String} user
  #
  # @returns {boolean} True if the annotation is private to the user.
  ###
  isPrivate: (permissions) ->
    user = session.state.userid
    user and angular.equals(permissions?.read or [], [user])

  ###*
  # @ngdoc method
  # @name permissions#permits
  #
  # @param {String} action action to authorize (read|update|delete|admin)
  # @param {Object} context to permit action on it or not
  # @param {String} user the userId
  #
  # User access-level-control function
  # TODO: this should move to the auth service and take multiple principals
  ###
  permits: (action, context, user) ->
    acl = _acl context

    for ace in acl
      if ace.principal not in [user, GROUP_WORLD]
        continue
      if ace.action not in [action, ALL_PERMISSIONS]
        continue
      return ace.allow

    false
]
