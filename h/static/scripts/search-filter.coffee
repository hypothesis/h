# This class will parse the search filter and produce a faceted search filter object
# It expects a search query string where the search term are separated by space character
# and collects them into the given term arrays
module.exports = class SearchFilter
  # Splits a search term into filter and data
  # i.e.
  #   'user:johndoe' -> ['user', 'johndoe']
  #   'example:text' -> [null, 'example:text']
  _splitTerm: (term) ->
    filter = term.slice 0, term.indexOf ":"
    unless filter?
      # The whole term is data
      return [null, term]

    if filter in ['group', 'quote', 'result', 'since',
                  'tag', 'text', 'uri', 'user']
      data = term[filter.length+1..]
      return [filter, data]
    else
      # The filter is not a power search filter, so the whole term is data
      return [null, term]

  # This function will slice the search-text input
  # Slice character: space,
  # but an expression between quotes (' or ") is considered one
  # I.e from the string: "text user:john 'to be or not to be' it will produce:
  # ["text", "user:john", "to be or not to be"]
  _tokenize: (searchtext) ->
    return [] unless searchtext

    # Small helper function for removing quote characters
    # from the beginning- and end of a string, if the
    # quote characters are the same.
    # I.e.
    #   'foo' -> foo
    #   "bar" -> bar
    #   'foo" -> 'foo"
    #   bar"  -> bar"
    _removeQuoteCharacter = (text) ->
      start = text.slice 0,1
      end = text.slice -1
      if (start is '"' or start is "'") and (start == end)
        text = text.slice 1, text.length - 1
      text

    tokens = searchtext.match /(?:[^\s"']+|"[^"]*"|'[^']*')+/g

    # Cut the opening and closing quote characters
    tokens = tokens.map _removeQuoteCharacter

    # Remove quotes for power search.
    # I.e. 'tag:"foo bar"' -> 'tag:foo bar'
    for token, index in tokens
      [filter, data] = @_splitTerm(token)
      if filter?
        tokens[index] = filter + ':' + (_removeQuoteCharacter data)

    tokens

  # Turns string query into object, where the properties are the search terms
  toObject: (searchtext) ->
    obj = {}
    filterToBackendFilter = (filter) ->
      if filter is 'tag'
        'tags'
      else
        filter

    addToObj = (key, data) ->
      if obj[key]?
        obj[key].push data
      else
        obj[key] = [data]

    if searchtext
      terms = @_tokenize(searchtext)
      for term in terms
        [filter, data] = @_splitTerm(term)
        unless filter?
          filter = 'any'
          data = term
        addToObj(filterToBackendFilter(filter), data)
    obj

  # This function will generate the facets from the search-text input
  # It'll first tokenize it and then sorts them into facet lists
  # The output will be a dict with the following structure:
  # An object with facet_names as keys.
  # A value for a key:
  # [facet_name]:
  #   [operator]: 'and'|'or'|'min' (for the elements of the facet terms list)
  #   [lowercase]: true|false
  #   [terms]: an array for the matched terms for this facet
  # The facet selection is done by analyzing each token.
  # It generally expects a <facet_name>:<facet_term> structure for a token
  # Where the facet names are: 'quote', 'result', 'since', 'tag', 'text', 'uri', 'user
  # Anything that didn't match go to the 'any' facet
  # For the 'since' facet the the time string is scanned and is converted to seconds
  # So i.e the 'since:7min' token will be converted to 7*60 = 420 for the since facet value
  generateFacetedFilter: (searchtext) ->
    any = []
    quote = []
    result = []
    since = []
    tag = []
    text = []
    uri = []
    user = []

    if searchtext
      terms = @_tokenize(searchtext)
      for term in terms
        filter = term.slice 0, term.indexOf ":"
        unless filter? then filter = ""
        switch filter
          when 'quote' then quote.push term[6..]
          when 'result' then result.push term[7..]
          when 'since'
            # We'll turn this into seconds
            time = term[6..].toLowerCase()
            if time.match /^\d+$/
              # Only digits, assuming seconds
              since.push time
            if time.match /^\d+sec$/
              # Time given in seconds
              t = /^(\d+)sec$/.exec(time)[1]
              since.push t
            if time.match /^\d+min$/
              # Time given in minutes
              t = /^(\d+)min$/.exec(time)[1]
              since.push t * 60
            if time.match /^\d+hour$/
              # Time given in hours
              t = /^(\d+)hour$/.exec(time)[1]
              since.push t * 60 * 60
            if time.match /^\d+day$/
              # Time given in days
              t = /^(\d+)day$/.exec(time)[1]
              since.push t * 60 * 60 * 24
            if time.match /^\d+week$/
              # Time given in week
              t = /^(\d+)week$/.exec(time)[1]
              since.push t * 60 * 60 * 24 * 7
            if time.match /^\d+month$/
              # Time given in month
              t = /^(\d+)month$/.exec(time)[1]
              since.push t * 60 * 60 * 24 * 30
            if time.match /^\d+year$/
              # Time given in year
              t = /^(\d+)year$/.exec(time)[1]
              since.push t * 60 * 60 * 24 * 365
          when 'tag' then tag.push term[4..]
          when 'text' then text.push term[5..]
          when 'uri' then uri.push term[4..]
          when 'user' then user.push term[5..]
          else any.push term

    any:
      terms: any
      operator: 'and'
    quote:
      terms: quote
      operator: 'and'
    result:
      terms: result
      operator: 'min'
    since:
      terms: since
      operator: 'and'
    tag:
      terms: tag
      operator: 'and'
    text:
      terms: text
      operator: 'and'
    uri:
      terms: uri
      operator: 'or'
    user:
      terms: user
      operator: 'or'
