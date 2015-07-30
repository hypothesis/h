{module, inject} = angular.mock

poem =
  tiger: 'Tiger! Tiger! burning bright
          In the forest of the night
          What immortal hand or eye
          Could frame thy fearful symmetry?'
  raven: 'Once upon a midnight dreary, while I pondered, weak and weary,
          Over many a quaint and curious volume of forgotten lore—
          While I nodded, nearly napping, suddenly there came a tapping,
          As of some one gently rapping, rapping at my chamber door.
          “’Tis some visitor,” I muttered, “tapping at my chamber door—
          Only this and nothing more.”'

describe 'viewFilter', ->
  sandbox = null
  fakeUnicode = null
  viewFilter = null

  before ->
    angular.module('h', [])
    .service('viewFilter', require('../view-filter'))


  beforeEach module('h')
  beforeEach module ($provide) ->
    sandbox = sinon.sandbox.create()

    fakeUnicode = {
      fold: sinon.stub().returnsArg(0)
      normalize: sinon.stub().returnsArg(0)
    }

    $provide.value('unicode', fakeUnicode)
    return

  beforeEach inject (_viewFilter_) ->
    viewFilter = _viewFilter_

  afterEach ->
    sandbox.restore()


  describe 'filter', ->
    it 'normalizes the filter terms', ->
      filters =
        text:
          terms: ['Tiger']
          operator: 'and'

      viewFilter.filter [], filters
      assert.calledWith fakeUnicode.fold, 'tiger'

    describe 'filter operators', ->
      annotations = null

      beforeEach ->
        annotations = [
          {id: 1, text: poem.tiger},
          {id: 2, text: poem.raven}
        ]

      it 'all terms must match for "and" operator', ->
        filters =
          text:
            terms: ['Tiger', 'burning', 'bright']
            operator: 'and'

        result = viewFilter.filter annotations, filters
        assert.equal result.length, 1
        assert.equal result[0], 1

      it 'only one term must match for "or" operator', ->
        filters =
          text:
            terms: ['Tiger', 'quaint']
            operator: 'or'

        result = viewFilter.filter annotations, filters
        assert.equal result.length, 2

    describe 'fields', ->
      describe 'autofalse', ->
        it 'consider auto false function', ->
          viewFilter.fields =
            test:
              autofalse: sandbox.stub().returns(true)
              value: (annotation) -> return annotation.test
              match: (term, value) -> return value.indexOf(term) > -1

          filters =
            test:
              terms: ['Tiger']
              operator: 'and'

          annotations = [{id: 1, test: poem.tiger}]

          result = viewFilter.filter annotations, filters
          assert.called viewFilter.fields.test.autofalse
          assert.equal result.length, 0

        it 'uses the value function to extract data from the annotation', ->
          viewFilter.fields =
            test:
              autofalse: (annotation) -> return false
              value: sandbox.stub().returns('test')
              match: (term, value) -> return value.indexOf(term) > -1

          filters =
            test:
              terms: ['test']
              operator: 'and'

          annotations = [{id: 1, test: poem.tiger}]

          result = viewFilter.filter annotations, filters
          assert.called viewFilter.fields.test.value
          assert.equal result.length, 1

        it 'the match function determines the matching', ->
          viewFilter.fields =
            test:
              autofalse: (annotation) -> return false
              value: (annotation) -> return annotation.test
              match: sandbox.stub().returns(false)

          filters =
            test:
              terms: ['Tiger']
              operator: 'and'

          annotations = [{id: 1, test: poem.tiger}]

          result = viewFilter.filter annotations, filters
          assert.called viewFilter.fields.test.match
          assert.equal result.length, 0

          viewFilter.fields.test.match.returns(true)
          result = viewFilter.filter annotations, filters
          assert.called viewFilter.fields.test.match
          assert.equal result.length, 1

    describe 'any field', ->
      it 'finds matches across many fields', ->
        annotation1 = {id: 1, text: poem.tiger}
        annotation2 = {id: 2, user: poem.tiger}
        annotation3 = {id: 3, tags: ['Tiger']}

        annotations = [annotation1, annotation2, annotation3]

        filters =
          any:
            terms: ['Tiger']
            operator: 'and'

        result = viewFilter.filter annotations, filters
        assert.equal result.length, 3

      it 'can find terms across different fields', ->
        annotation =
          id:1
          text: poem.tiger
          target: [
            selector: [{
              "type": "TextQuoteSelector",
              "exact": "The Tiger by William Blake",
            }]
          user: "acct:poe@edgar.com"
          tags: ["poem", "Blake", "Tiger"]
          ]

        filters =
          any:
            terms: ['burning', 'William', 'poem', 'bright']
            operator: 'and'

        result = viewFilter.filter [annotation], filters
        assert.equal result.length, 1
        assert.equal result[0], 1
