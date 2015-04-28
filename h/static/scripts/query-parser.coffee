# This class will process the results of search and generate the correct filter
# It expects the following dict format as rules
# { facet_name : {
#      formatter: to format the value (optional)
#      path: json path mapping to the annotation field
#      case_sensitive: true|false (default: false)
#      and_or: and|or for multiple values should it threat them as 'or' or 'and' (def: or)
#      operator: if given it'll use this operator regardless of other circumstances
#
#      options: backend specific options
#      options.es: elasticsearch specific options
#      options.es.query_type : can be: simple (term), query_string, match, multi_match
#         defaults to: simple, determines which es query type to use
#      options.es.cutoff_frequency: if set, the query will be given a cutoff_frequency for this facet
#      options.es.and_or: match and multi_match queries can use this, defaults to and
#      options.es.match_type: multi_match query type
#      options.es.fields: fields to search for in multi-match query
# }
# The models is the direct output from visualsearch
module.exports = class QueryParser
  rules:
    user:
      path: '/user'
      and_or: 'or'
    text:
      path: '/text'
      and_or: 'and'
    tag:
      path: '/tags'
      and_or: 'and'
    quote:
      path: '/quote'
      and_or: 'and'
    uri:
      formatter: (uri) ->
        uri.toLowerCase()
      path: '/uri'
      and_or: 'or'
      options:
        es:
         query_type: 'match'
         cutoff_frequency: 0.001
         and_or: 'and'
    since:
      formatter: (past) ->
        seconds =
          switch past
            when '5 min' then 5*60
            when '30 min' then 30*60
            when '1 hour' then 60*60
            when '12 hours' then 12*60*60
            when '1 day' then 24*60*60
            when '1 week' then 7*24*60*60
            when '1 month' then 30*24*60*60
            when '1 year' then 365*24*60*60
        new Date(new Date().valueOf() - seconds*1000)
      path: '/created'
      and_or: 'and'
      operator: 'ge'
    any:
      and_or: 'and'
      path:   ['/quote', '/tags', '/text', '/uri', '/user']
      options:
        es:
         query_type: 'multi_match'
         match_type: 'cross_fields'
         and_or: 'and'
         fields:   ['quote', 'tags', 'text', 'uri.parts', 'user']

  populateFilter: (filter, query) =>
    # Populate a filter with a query object
    for category, value of query
      unless @rules[category]? then continue
      terms = value.terms
      unless terms.length then continue
      rule = @rules[category]

      # Now generate the clause with the help of the rule
      case_sensitive = if rule.case_sensitive? then rule.case_sensitive else false
      and_or = if rule.and_or? then rule.and_or else 'or'
      mapped_field = if rule.path? then rule.path else '/'+category

      if and_or is 'or'
        oper_part = if rule.operator? then rule.operator else 'match_of'

        value_part = []
        for term in terms
          t = if rule.formatter then rule.formatter term else term
          value_part.push t

        filter.addClause mapped_field, oper_part, value_part, case_sensitive, rule.options
      else
        oper_part = if rule.operator? then rule.operator else 'matches'
        for val in terms
          value_part = if rule.formatter then rule.formatter val else val
          filter.addClause mapped_field, oper_part, value_part, case_sensitive, rule.options
