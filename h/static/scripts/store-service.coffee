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
angular.module('h')
.service('store', [
  '$document', '$http', '$resource',
  ($document,   $http,   $resource) ->

    # Find any service link tag
    svc = $document.find('link')
    .filter -> @rel is 'service' and @type is 'application/annotatorsvc+json'
    .filter -> @href
    .prop('href') or ''

    camelize = (string) ->
      string.replace /(?:^|_)([a-z])/g, (_, char) -> char.toUpperCase()

    store =
      $resolved: false
      # We call the service_url and the backend api gives back
      # the actions and urls it provides.
      $promise: $http.get(svc)
        .finally -> store.$resolved = true
        .then (response) ->
          for name, actions of response.data.links
            # For each action name we configure an ng-resource.
            # For the search resource, one URL is given for all actions.
            # For the annotations, each action has its own URL.
            prop = "#{camelize(name)}Resource"
            store[prop] = $resource(actions.url or svc, {}, actions)
          store
])
