minute = 60
hour = minute * 60
day = hour * 24
month = day * 30
year = day * 365

BREAKPOINTS = [
  [30,         'moments ago',    1     ]
  [minute,     '{} seconds ago', 1     ]
  [2 * minute, 'a minute ago',   minute]
  [hour,       '{} minutes ago', minute]
  [2 * hour,   'an hour ago',    hour  ]
  [day,        '{} hours ago',   hour  ]
  [2 * day,    'yesterday',      day   ]
  [month,      '{} days ago',    day   ]
  [year,       '{} months ago',  month ]
  [Infinity,   '{} years ago',   year  ]
]

arrayFind = (array, predicate) ->
  if not array?
    throw new TypeError('arrayFindIndex called on null or undefined')
  if typeof predicate != 'function'
    throw new TypeError('predicate must be a function')

  for value, i in array
    if predicate(value, i, array)
      return value

  return null

getBreakpoint = (date) ->
  delta = Math.round((new Date() - new Date(date)) / 1000)

  delta: delta
  breakpoint: arrayFind(BREAKPOINTS, (x) -> x[0] > delta)


createTimeHelpers = ->
  toFuzzyString: (date) ->
    return '' unless date
    {delta, breakpoint} = getBreakpoint(date)
    return '' unless breakpoint
    template = breakpoint[1]
    resolution = breakpoint[2]
    return template.replace('{}', String(Math.floor(delta / resolution)))

  nextFuzzyUpdate: (date) ->
    return null if not date
    {_, breakpoint} = getBreakpoint(date)
    return null unless breakpoint
    return breakpoint[2]

angular.module('h.helpers')
.factory('timeHelpers', createTimeHelpers)
