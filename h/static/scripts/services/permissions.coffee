###*
# @ngdoc service
# @name  Permissions
#
# @description
# This service can set default permissions to annotations properly and
# offers some utility functions regarding those.
###
class Permissions
  GROUP_WORLD = 'group:__world__'
  EVERYONE = 'Everyone'
  ALL_PERMISSIONS = 'ALL_PERMISSIONS'

  this.$inject = ['auth']
  constructor:    (auth) ->
    ###*
    # @ngdoc method
    # @name permissions#private
    #
    # Sets permissions for a private annotation
    # Typical use: annotation.permissions = permissions.private()
    ###
    @private = ->
      return {
        read: [auth.user]
        update: [auth.user]
        delete: [auth.user]
        admin: [auth.user]
      }

    ###*
    # @ngdoc method
    # @name permissions#private
    #
    # Sets permissions for a public annotation
    # Typical use: annotation.permissions = permissions.public()
    ###
    @public = ->
      return {
        read: [GROUP_WORLD]
        update: [auth.user]
        delete: [auth.user]
        admin: [auth.user]
      }

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
  isPrivate: (permissions, user) ->
    user and angular.equals(permissions?.read or [], [user])

  # Creates access-level-control object list
  _acl = (context) ->
    acl = []

    for action, roles of context.permissions or []
      for role in roles
        allow = true
        if role.indexOf('group:') is 0
          if role == GROUP_WORLD
            principal = EVERYONE
          else
            # unhandled group
            allow = false
            principal = role
        else
          if role.indexOf('acct:') is 0
            principal = role
          else
            allow = false
            principal = role

        acl.push
          allow: allow
          principal: principal
          action: action

    if acl.length
      acl
    else
      return [
        allow: true
        principal: EVERYONE
        action: ALL_PERMISSIONS
      ]

  ###*
  # @ngdoc method
  # @name permissions#permits
  #
  # @param {String} action action to authorize (read|update|delete|admin)
  # @param {Object} context to permit action on it or not
  # @param {String} user the userId
  #
  # User access-level-control function
  ###
  permits: (action, context, user) ->
    acls = _acl context

    for acl in acls
      if acl.principal not in [user, EVERYONE]
        continue
      if acl.action not in [action, ALL_PERMISSIONS]
        continue
      return acl.allow

    false


angular.module('h')
.service('permissions', Permissions)
