class Converter extends Markdown.Converter
  constructor: ->
    super
    this.hooks.chain "preConversion", (text) ->
      if text then text else ""
    this.hooks.chain "postConversion", (text) ->
      text.replace /<a href=/g, "<a target=\"_blank\" href="


momentFilter = ->
  (value, format) ->
    # Determine the timezone name and browser language.
    timezone = jstz.determine().name()
    userLang = navigator.language || navigator.userLanguage

    # Now make a localized date and set the language.
    momentDate = moment value
    momentDate.lang userLang

    # Try to localize to the browser's timezone.
    try
      momentDate.tz(timezone).format('LLLL')
    catch error
      # For an invalid timezone, use the default.
      momentDate.format('LLLL')


persona = (user, part='username') ->
  part = ['term', 'username', 'provider'].indexOf(part)
  (user?.match /^acct:([^@]+)@(.+)/)?[part]


angular.module('h')
.filter('converter', -> (new Converter()).makeHtml)
.filter('moment', momentFilter)
.filter('persona', -> persona)
