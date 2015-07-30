var angular = require('angular');

var configureHttp = require('./http');
var configureIdentity = require('./identity');

module.exports = angular.module('h')
.config(configureHttp)
.config(configureIdentity)
;
