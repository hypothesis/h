FIELDS = ['quote', 'result', 'since', 'tag', 'text', 'uri', 'user']


# Tokenize text, treating quoted sections as a single token.
tokenize = (searchtext) ->
  groups = searchtext.match(/((?:[^\s]+:)?"[^"]*")|([^\s"]+)/g)
  if groups
    return groups
  else
    return []


# Splits a search term into a field and a value.
# Returns an Array of the field (possibly null) and the value.
splitTerm = (term) ->
  field = term.slice 0, term.indexOf ":"

  if field? and field in FIELDS
    value = term[field.length+1..]
    return [field, value]
  else
    return [null, term]


# Remove matching quotes around a string.
unquote = (text) ->
  start = text.slice(0, 1)
  end = text.slice(-1)
  if start is '"' and start is end
    return text = text.slice(1, text.length - 1)
  else
    return text


# Parse query for field:value terms putting the remainder in the 'any' field.
module.exports = (query='') ->
  result = {}

  for term in tokenize(query)
    [field, value] = splitTerm(term)

    if field?
      value = unquote(value)
    else
      field = 'any'
      value = unquote(term)

    result[field] ?= []
    result[field].push(value)

  return result
