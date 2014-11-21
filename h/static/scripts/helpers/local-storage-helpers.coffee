# Minimal wrapping around the localStorage service

# Visibility constants
PRIVACY_KEY = 'hypothesis.privacy'

createLocalStorageHelpers = [
  '$window'
  ($window) ->
    # Detection is needed because we run often as a third party widget and
    # third party storage blocking often blocks cookies and local storage
    # https://github.com/Modernizr/Modernizr/blob/master/feature-detects/storage/localstorage.js
    hasStorage = do ->
        key = 'hypothesis.testKey'
        try
          $window.localStorage.setItem key, key
          $window.localStorage.removeItem key
          true
        catch exception
          false

    VISIBILITY_PUBLIC: 'public'
    VISIBILITY_PRIVATE: 'private'

    setVisibility: (privacy) ->
      if hasStorage
        $window.localStorage[PRIVACY_KEY] = privacy

    getVisibility: ->
      if hasStorage
        return $window.localStorage[PRIVACY_KEY]
      else
        undefined
]

angular.module('h.helpers')
.service('localStorageHelpers', createLocalStorageHelpers)
