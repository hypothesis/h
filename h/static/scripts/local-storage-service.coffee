localStorageProvider = ->
  $get: ['$window', ($window) ->
    # Detection is needed because we run often as a third party widget and
    # third party storage blocking often blocks cookies and local storage
    # https://github.com/Modernizr/Modernizr/blob/master/feature-detects/storage/localstorage.js
    storage = do ->
      key = 'hypothesis.testKey'
      try
        $window.localStorage.setItem  key, key
        $window.localStorage.removeItem key
        $window.localStorage
      catch
        memoryStorage = {}
        getItem: (key) ->
          if key of memoryStorage then memoryStorage[key] else null
        setItem: (key, value) ->
          memoryStorage[key] = value
        removeItem: (key) ->
          delete memoryStorage[key]

    return {
      getItem: (key) ->
        storage.getItem key
      getObject: (key) ->
        json = storage.getItem key
        return JSON.parse json if json
        null
      setItem: (key, value) ->
        storage.setItem key, value
      setObject: (key, value) ->
        repr = JSON.stringify value
        storage.setItem key, repr
      removeItem: (key) ->
        storage.getItem key
    }
  ]

angular.module('h')
.provider('localstorage', localStorageProvider)
