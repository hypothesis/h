FEATURES = {
  accounts: """{{ feature('accounts') | json }}""",
  notification: """{{ feature('notification') | json }}""",
  streamer: """{{ feature('streamer') | json }}"""
}


feature = (name) ->
  value = FEATURES[name]
  if value?
    return !!value
  else
    throw new Error("unknown feature: #{name}")


config = (fn) ->
  module.exports.config(fn)


angular = require('angular')
module.exports = angular.module('h.config').value('feature', feature)

if feature('accounts')
  config(require('./accounts'))
