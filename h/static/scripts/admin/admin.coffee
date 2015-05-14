angular = require('angular')

angular.module('h')
.provider('admin', require('./admin-service'))

require('./admin-controller')
