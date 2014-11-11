createTimeHelpers = ->
  timestamp: (date) ->
    return {message: '', updateAt: 5} if not date
    delta = Math.round((+new Date - new Date(date)) / 1000)

    minute = 60
    hour = minute * 60
    day = hour * 24
    month = day * 30
    year = day * 365

    if (delta < 30)
      message = 'moments ago'
      updateAt = 30 - delta
    else if (delta < minute)
      message = delta + ' seconds ago'
      updateAt = 1
     else if (delta < 2 * minute)
      message = 'a minute ago'
      updateAt = 2*minute - delta
     else if (delta < hour)
      message = Math.floor(delta / minute) + ' minutes ago'
      updateAt = minute
     else if (Math.floor(delta / hour) == 1)
      message = '1 hour ago'
      updateAt = hour
     else if (delta < day)
      message = Math.floor(delta / hour) + ' hours ago'
      updateAt = hour
     else if (delta < day * 2)
      message = 'yesterday'
      updateAt = 2*day - delta
     else if (delta < month)
      message = Math.round(delta / day) + ' days ago'
      updateAt = day
     else if (delta < year)
      message = Math.round(delta / month) + ' months ago'
      updateAt = month
     else
      message = Math.round(delta / year) + ' years ago'
      updateAt= year

    message: message
    updateAt: updateAt

angular.module('h.helpers')
.factory('timeHelpers', createTimeHelpers)