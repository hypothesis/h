class Converter extends Markdown.Converter
  constructor: ->
    super
    this.hooks.chain "preConversion", (text) ->
      if text then text else ""
    this.hooks.chain "postConversion", (text) ->
      text.replace /<a href=/g, "<a target=\"_blank\" href="


fuzzyTime = (date, next = false) ->
  return '' if not date
  delta = Math.round((+new Date - new Date(date)) / 1000)

  minute = 60
  hour = minute * 60
  day = hour * 24
  week = day * 7
  month = day * 30
  year = day * 365

  if (delta < 30)
    fuzzy = 'moments ago'
    nextUpdate = 30 - delta
  else if (delta < minute)
    fuzzy = delta + ' seconds ago'
    nextUpdate = 1
   else if (delta < 2 * minute)
    fuzzy = 'a minute ago'
    nextUpdate = 2*minute - delta
   else if (delta < hour)
    fuzzy = Math.floor(delta / minute) + ' minutes ago'
    nextUpdate = minute
   else if (Math.floor(delta / hour) == 1)
    fuzzy = '1 hour ago'
    nextUpdate = hour
   else if (delta < day)
    fuzzy = Math.floor(delta / hour) + ' hours ago'
    nextUpdate = hour
   else if (delta < day * 2)
    fuzzy = 'yesterday'
    nextUpdate = 2*day - delta
   else if (delta < month)
    fuzzy = Math.round(delta / day) + ' days ago'
    nextUpdate = day
   else if (delta < year)
    fuzzy = Math.round(delta / month) + ' months ago'
    nextUpdate = month
   else
    fuzzy = Math.round(delta / year) + ' years ago'
    nextUpdate = year

  if next
    nextUpdate
  else
    fuzzy


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
.filter('fuzzyTime', -> fuzzyTime)
.filter('moment', momentFilter)
.filter('persona', -> persona)
