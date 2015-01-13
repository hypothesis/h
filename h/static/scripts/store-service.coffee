angular.module('h')
.service('store', [
  '$document', '$http', '$resource',
  ($document,   $http,   $resource) ->
    svc = $document.find('link')
    .filter -> @rel is 'service' and @type is 'application/annotatorsvc+json'
    .filter -> @href
    .prop('href')

    store =
      $resolved: false
      $promise: $http.get(svc)
        .finally -> store.$resolved = true
        .then (response) ->
          for name, actions of response.data.links
            store[name] = $resource(actions.url or svc, {}, actions)
          store
])
