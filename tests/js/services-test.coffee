assert = chai.assert
sinon.assert.expose assert, prefix: null

describe 'h', ->
  sandbox = null

  beforeEach module('h')

  beforeEach module ($provide) ->
    sandbox = sinon.sandbox.create()
    return

  afterEach ->
    sandbox.restore()

  describe 'viewFilter service', ->
    fakeStringHelpers = null
    viewFilter = null

    beforeEach module ($provide) ->
      fakeStringHelpers = {
        uniFold: sandbox.spy()
      }

      $provide.value 'stringHelpers', fakeStringHelpers
      return

    beforeEach inject (_viewFilter_) ->
      viewFilter = _viewFilter_

    describe '_normalize', ->
      it 'calls stringHelpers.uniFold with a string argument', ->
        text = 'I heard you”—here I opened wide the door;—
               Darkness there and nothing more.'
        viewFilter._normalize text
        assert.calledWith fakeStringHelpers.uniFold, text

      it 'returns the argument otherwise', ->
        input = null
        result = viewFilter._normalize input
        assert.notCalled fakeStringHelpers.uniFold
        assert.deepEqual result, input

        input = {}
        result = viewFilter._normalize input
        assert.notCalled fakeStringHelpers.uniFold
        assert.deepEqual result, input

        input = 2
        result = viewFilter._normalize input
        assert.notCalled fakeStringHelpers.uniFold
        assert.deepEqual result, input

    describe 'match functions', ->
      filter = {
        terms: ['Tiger', 'burning', 'bright']
        operator: 'and'
      }

      matchAllFn = (term, value) -> true
      matchNoneFn = (term, value) -> false

      describe '_matches', ->
        matchFn = (term, value) -> value.indexOf(term) > -1

        beforeEach ->
          fakeStringHelpers.uniFold = (e) -> return e

        it 'uses the match function to evaluate matching', ->
          match = viewFilter._matches filter, null, matchAllFn
          assert.isTrue match

          match = viewFilter._matches filter, null, matchNoneFn
          assert.isFalse match

        it 'all terms must match for "and" operator', ->
          value = 'Tiger! Tiger! burning bright
                  In the forest of the night
                  What immortal hand or eye
                  Could frame thy fearful symmetry?'
          match = viewFilter._matches filter, value, matchFn
          assert.isTrue match

          value = "burning bright In the forest of the night"
          match = viewFilter._matches filter, value, matchFn
          assert.isFalse match

        it 'only one term match is enough for "or" operator', ->
          filter.operator = 'or'
          value = 'Tiger! Tiger!'
          match = viewFilter._matches filter, value, matchFn
          assert.isTrue match

      describe '_arrayMatches', ->
        matchFn = (term, value) -> value in term

        it 'uses the match function to evaluate matching', ->
          value = ['copycat']
          match = viewFilter._arrayMatches filter, value, matchAllFn
          assert.isTrue match

          match = viewFilter._arrayMatches filter, value, matchNoneFn
          assert.isFalse match

        it 'all terms must match for "and" operator', ->
          filter.operator = 'and'

          value = ['Tiger', 'burning', 'in the forest', 'bright']
          match = viewFilter._arrayMatches filter, value, matchFn
          assert.isTrue match

          value = ['Tiger', 'burning', 'in the forest']
          match = viewFilter._arrayMatches filter, value, matchFn
          assert.isFalse match

        it 'only one term match is enough for "or" operator', ->
          filter.operator = 'or'
          value = ['Tiger', 'in the forest']
          match = viewFilter._arrayMatches filter, value, matchFn
          assert.isTrue match

      describe '_checkMatch', ->
        checker = {
          autofalse: (obj) -> not obj.text?
          value: (obj) -> obj.text
          match: (term, value) -> value.indexOf(term) > -1
        }

        it 'returns false if autofalseFn returns false', ->
          annotation = {}
          result = viewFilter._checkMatch filter, annotation, checker
          assert.isFalse result

        it 'calls _matches() for scalar values', ->
          annotation = {
            text: 'In what distant deeps or skies
                  Burnt the fire of thine eyes?
                  On what wings dare he aspire?
                  What the hand dare seize the fire?'
          }

          viewFilter._matches = sandbox.spy()
          viewFilter._checkMatch filter, annotation, checker
          assert.called viewFilter._matches

        it 'calls _arrayMatches() for arrays', ->
          annotation = {
            text: ['In what distant deeps or skies',
                  'Burnt the fire of thine eyes?']
          }

          viewFilter._arrayMatches = sandbox.spy()
          viewFilter._checkMatch filter, annotation, checker
          assert.called viewFilter._arrayMatches

