angular = require('angular')

module.exports = class AdminService
  actions: null
  options: null

  constructor: ->
    @actions =
      set_nipsa:
        method: 'POST'
        withCredentials: true

    @options = {}

  $get: [
    '$document', '$http', '$q', '$resource',
    ($document,   $http,   $q,   $resource) ->
      actions = {}
      provider = this

      prepare = (data) ->
        return angular.toJson data

      process = (data) ->
        # Parse as json
        data = angular.fromJson data

        # Lift response data
        model = data.model or {}
        model.errors = data.errors
        model.reason = data.reason

        # Return the model
        model

      for name, options of provider.actions
        actions[name] = angular.extend {}, options, @options
        actions[name].transformRequest = prepare
        actions[name].transformResponse = process

      base = $document.prop('baseURI')
      endpoint = new URL('/admin/settings', base).href
      $resource(endpoint, {}, actions)
  ]
