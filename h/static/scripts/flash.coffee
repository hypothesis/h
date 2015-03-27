module.exports = ['toastr', (toastr) ->
  info: angular.bind(toastr, toastr.info)
  success: angular.bind(toastr, toastr.success)
  warning: angular.bind(toastr, toastr.warning)
  error: angular.bind(toastr, toastr.error)
]
