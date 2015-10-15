###*
# @ngdoc service
# @name store
#
# @description
# The `store` service handles the backend calls for the restful API. This is
# created dynamically from the API index as the angular $resource() method
# supports the same keys as the index document. This will make a resource
# constructor for each endpoint eg. store.AnnotationResource() and
# store.SearchResource().
###
module.exports = [
  '$http', '$resource', 'settings'
  ($http,   $resource,   settings) ->
    camelize = (string) ->
      string.replace /(?:^|_)([a-z])/g, (_, char) -> char.toUpperCase()

    store =
      $resolved: false
      # We call the API root and it gives back the actions it provides.
      $promise: $http.get(settings.apiUrl)
        .finally -> store.$resolved = true
        .then (response) ->
          for name, actions of response.data.links
            # For each action name we configure an ng-resource.
            # For the search resource, one URL is given for all actions.
            # For the annotations, each action has its own URL.
            prop = "#{camelize(name)}Resource"
            store[prop] = $resource(actions.url or settings.apiUrl, {}, actions)
          store
]
