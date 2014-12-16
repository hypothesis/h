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

angular.module('h')
.service('permissions', Permissions)