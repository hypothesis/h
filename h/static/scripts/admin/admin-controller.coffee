class AdminController
  @inject = [  '$scope', '$filter',
               'admin', 'auth', 'flash', 'formRespond', 'identity']
  constructor: ($scope,   $filter,
                admin,   auth,   flash,   formRespond,   identity) ->

    onError = (form, response) ->
      if response.status >= 400 and response.status < 500
        formRespond(form, response.data.errors)
      else
        flash.error(response.reason ? 'Sorry, we were unable to perform your request')

      $scope.$broadcast 'formState', form.$name, ''  # Update status btn

    onSuccess = (form, response) ->
      if response.errors # This is not a real success
        onError(form, response)
        return

      form.$setPristine()
      formModel = form.$name.slice(0, -4)
      $scope[formModel] = {} # Reset form fields.
      $scope.$broadcast 'formState', form.$name, 'success'  # Update status btn

    $scope.submit = (form, value) ->
      formRespond(form)
      return unless form.$valid

      username = form.username.$modelValue

      packet = {}
      packet[username] = nipsa: value

      successHandler = angular.bind(null, onSuccess, form)
      errorHandler   = angular.bind(null, onError, form)

      $scope.$broadcast 'formState', form.$name, 'loading'  # Update status btn
      promise = admin.set_nipsa(packet)
      promise.$promise.then(successHandler, errorHandler)

angular.module('h')
.controller('AdminController', AdminController)
