/*
 * http://stackoverflow.com/a/7641812
 */
var Handlebars

Handlebars.registerHelper('fuzzyTime', function (date) {
  if (!date) return ''
  var delta = Math.round((+new Date - new Date(date)) / 1000)

  var minute = 60,
  hour = minute * 60,
  day = hour * 24,
  week = day * 7,
  month = day * 30

  var fuzzy

  if (delta < 30) {
    fuzzy = 'moments ago.'
  } else if (delta < minute) {
    fuzzy = delta + ' seconds ago.'
  } else if (delta < 2 * minute) {
    fuzzy = 'a minute ago.'
  } else if (delta < hour) {
    fuzzy = Math.floor(delta / minute) + ' minutes ago.'
  } else if (Math.floor(delta / hour) == 1) {
    fuzzy = '1 hour ago.'
  } else if (delta < day) {
    fuzzy = Math.floor(delta / hour) + ' hours ago.'
  } else if (delta < day * 2) {
    fuzzy = 'yesterday'
  } else if (delta < month) {
    fuzzy = Math.round(delta / day) + ' days ago'
  } else {
    fuzzy = new Date(date).toLocaleDateString()
  }

  return fuzzy
})

Handlebars.registerHelper('splitUser', function (user, options) {
  var parts = this.user.split(/(?:acct:)|@/);
  return options.fn({
    name: parts[1],
    provider: parts[2]
  })
})

Handlebars.registerHelper('formatUser', function (user) {
  return new Handlebars.SafeString(
    user.replace(
        /^acct:([^@]+)@(.+)$/,
      '$1 <span class="provider">on $2</span>'))
})
