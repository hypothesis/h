module.exports = ['localStorage', (localStorage) ->
  TAGS_LIST_KEY = 'hypothesis.user.tags.list'
  TAGS_MAP_KEY = 'hypothesis.user.tags.map'

  filter: (query) ->
    savedTags = localStorage.getObject TAGS_LIST_KEY
    savedTags ?= []

    # Only show tags having query as a substring
    filterFn = (e) ->
      e.toLowerCase().indexOf(query.toLowerCase()) > -1

    savedTags.filter(filterFn)

  # Add newly added tags from an annotation to the stored ones and refresh
  # timestamp for every tags used.
  store: (tags) ->
    savedTags = localStorage.getObject TAGS_MAP_KEY
    savedTags ?= {}

    for tag in tags
      if savedTags[tag.text]?
        # Update counter and timestamp
        savedTags[tag.text].count += 1
        savedTags[tag.text].updated = Date.now()
      else
        # Brand new tag, create an entry for it
        savedTags[tag.text] = {
          text: tag.text
          count: 1
          updated: Date.now()
        }

    localStorage.setObject TAGS_MAP_KEY, savedTags

    tagsList = []
    for tag of savedTags
      tagsList[tagsList.length] = tag

    # Now produce TAGS_LIST, ordered by (count desc, lexical asc)
    compareFn = (t1, t2) ->
      if savedTags[t1].count != savedTags[t2].count
        return savedTags[t2].count - savedTags[t1].count
      else
        return -1 if t1 < t2
        return 1 if t1 > t2
        return 0

    tagsList = tagsList.sort(compareFn)
    localStorage.setObject TAGS_LIST_KEY, tagsList
]
