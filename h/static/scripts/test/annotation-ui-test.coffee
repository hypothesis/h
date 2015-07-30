{module, inject} = angular.mock

describe 'annotationUI', ->
  annotationUI = null

  before ->
    angular.module('h', [])
    .service('annotationUI', require('../annotation-ui'))

  beforeEach module('h')
  beforeEach inject (_annotationUI_) ->
    annotationUI = _annotationUI_

  describe '.focusAnnotations()', ->
    it 'adds the passed annotations to the focusedAnnotationMap', ->
      annotationUI.focusAnnotations([{$$tag: 1}, {$$tag: 2}, {$$tag: 3}])
      assert.deepEqual(annotationUI.focusedAnnotationMap, {
        1: true, 2: true, 3: true
      })

    it 'replaces any annotations originally in the map', ->
      annotationUI.focusedAnnotationMap = {1: true}
      annotationUI.focusAnnotations([{$$tag: 2}, {$$tag: 3}])
      assert.deepEqual(annotationUI.focusedAnnotationMap, {
        2: true, 3: true
      })

    it 'does not modify the original map object', ->
      orig = annotationUI.focusedAnnotationMap = {1: true}
      annotationUI.focusAnnotations([{$$tag: 2}, {$$tag: 3}])
      assert.notEqual(annotationUI.focusedAnnotationMap, orig)

    it 'nulls the map if no annotations are focused', ->
      orig = annotationUI.focusedAnnotationMap = {$$tag: true}
      annotationUI.focusAnnotations([])
      assert.isNull(annotationUI.focusedAnnotationMap)

  describe '.hasSelectedAnnotations', ->
    it 'returns true if there are any selected annotations', ->
      annotationUI.selectedAnnotationMap = {1: true}
      assert.isTrue(annotationUI.hasSelectedAnnotations())

    it 'returns false if there are no selected annotations', ->
      annotationUI.selectedAnnotationMap = null
      assert.isFalse(annotationUI.hasSelectedAnnotations())

  describe '.isAnnotationSelected', ->
    it 'returns true if the id provided is selected', ->
      annotationUI.selectedAnnotationMap = {1: true}
      assert.isTrue(annotationUI.isAnnotationSelected(1))

    it 'returns false if the id provided is not selected', ->
      annotationUI.selectedAnnotationMap = {1: true}
      assert.isFalse(annotationUI.isAnnotationSelected(2))

    it 'returns false if there are no selected annotations', ->
      annotationUI.selectedAnnotationMap = null
      assert.isFalse(annotationUI.isAnnotationSelected(1))

  describe '.selectAnnotations()', ->
    it 'adds the passed annotations to the selectedAnnotationMap', ->
      annotationUI.selectAnnotations([{id: 1}, {id: 2}, {id: 3}])
      assert.deepEqual(annotationUI.selectedAnnotationMap, {
        1: true, 2: true, 3: true
      })

    it 'replaces any annotations originally in the map', ->
      annotationUI.selectedAnnotationMap = {1: true}
      annotationUI.selectAnnotations([{id: 2}, {id: 3}])
      assert.deepEqual(annotationUI.selectedAnnotationMap, {
        2: true, 3: true
      })

    it 'does not modify the original map object', ->
      orig = annotationUI.selectedAnnotationMap = {1: true}
      annotationUI.selectAnnotations([{id: 2}, {id: 3}])
      assert.notEqual(annotationUI.selectedAnnotationMap, orig)

    it 'nulls the map if no annotations are selected', ->
      orig = annotationUI.selectedAnnotationMap = {1: true}
      annotationUI.selectAnnotations([])
      assert.isNull(annotationUI.selectedAnnotationMap)

  describe '.xorSelectedAnnotations()', ->
    it 'adds annotations missing from the selectedAnnotationMap', ->
      annotationUI.selectedAnnotationMap = {1: true, 2: true}
      annotationUI.xorSelectedAnnotations([{id: 3}, {id: 4}])
      assert.deepEqual(annotationUI.selectedAnnotationMap, {
        1: true, 2: true, 3: true, 4: true
      })

    it 'removes annotations already in the selectedAnnotationMap', ->
      annotationUI.selectedAnnotationMap = {1: true, 3: true}
      annotationUI.xorSelectedAnnotations([{id: 1}, {id: 2}])
      assert.deepEqual(annotationUI.selectedAnnotationMap, 2:true, 3: true)

    it 'does not modify the original map object', ->
      orig = annotationUI.selectedAnnotationMap = {1: true}
      annotationUI.xorSelectedAnnotations([{id: 2}, {id: 3}])
      assert.notEqual(annotationUI.selectedAnnotationMap, orig)

    it 'nulls the map if no annotations are selected', ->
      orig = annotationUI.selectedAnnotationMap = {1: true}
      annotationUI.xorSelectedAnnotations([id: 1])
      assert.isNull(annotationUI.selectedAnnotationMap)

  describe '.removeSelectedAnnotation', ->
    it 'removes an annotation from the selectedAnnotationMap', ->
      annotationUI.selectedAnnotationMap = {1: true, 2: true, 3: true}
      annotationUI.removeSelectedAnnotation(id: 2)
      assert.deepEqual(annotationUI.selectedAnnotationMap, {
        1: true, 3: true
      })

    it 'does not modify the original map object', ->
      orig = annotationUI.selectedAnnotationMap = {1: true}
      annotationUI.removeSelectedAnnotation(id: 1)
      assert.notEqual(annotationUI.selectedAnnotationMap, orig)

    it 'nulls the map if no annotations are selected', ->
      orig = annotationUI.selectedAnnotationMap = {1: true}
      annotationUI.removeSelectedAnnotation(id: 1)
      assert.isNull(annotationUI.selectedAnnotationMap)

  describe '.clearSelectedAnnotations', ->
    it 'removes all annotations from the selection', ->
      annotationUI.selectedAnnotationMap = {1: true, 2: true, 3: true}
      annotationUI.clearSelectedAnnotations()
      assert.isNull(annotationUI.selectedAnnotationMap)
