###*
# @ngdoc service
# @name  Permissions
#
# @description
# This service can set default permissions to annotations properly and
# offers some utility functions regarding those.
###
class Permissions
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
        read: ['group:__world__']
        update: [auth.user]
        delete: [auth.user]
        admin: [auth.user]
      }

  ###*
  # @ngdoc method
  # @name permissions#isPublic
  #
  # @param {Object} annotation annotation to check permissions
  #
  # This function determines whether the annotation is publicly
  # visible(readable) or not.
  ###
  isPublic: (annotation) ->
    'group:__world__' in (annotation.permissions?.read or [])

  ###*
  # @ngdoc method
  # @name permissions#permits
  #
  # @param {String} action action to authorize (read|update|delete|admin)
  # @param {Object} annotation to permit action on it or not
  # @param {String} user the userId
  #
  # User authorization function used by (not solely) the Permissions plugin
  ###
  permits: (action, annotation, user) ->
    if annotation.permissions
      tokens = annotation.permissions[action] || []

      if tokens.length == 0
        # Empty or missing tokens array: only admin can perform action.
        return false

      for token in tokens
        if user == token
          return true
        if token == 'group:__world__'
          return true

      # No tokens matched: action should not be performed.
      return false

    # Coarse-grained authorization
    else if annotation.user
      return user and user == annotation.user

    # No authorization info on annotation: free-for-all!
    true


angular.module('h')
.service('permissions', Permissions)
