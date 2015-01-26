assert = chai.assert
sinon.assert.expose(assert, prefix: '')

describe 'AnnotationUI', ->
  annotationUI = null

  beforeEach module('h')
  beforeEach inject (_annotationUI_) ->
    annotationUI = _annotationUI_

  describe '.focusAnnotations()', ->
    it 'adds the passed annotations to the focusedAnnotationMap', ->
      annotationUI.focusAnnotations([{id: 1}, {id: 2}, {id: 3}])
      assert.deepEqual(annotationUI.focusedAnnotationMap, {
        1: true, 2: true, 3: true
      })

    it 'replaces any annotations originally in the map', ->
      annotationUI.focusedAnnotationMap = {1: true}
      annotationUI.focusAnnotations([{id: 2}, {id: 3}])
      assert.deepEqual(annotationUI.focusedAnnotationMap, {
        2: true, 3: true
      })

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

  describe '.xorSelectedAnnotations()', ->
    it 'adds annotations missing from the selectedAnnotationMap', ->
      annotationUI.selectedAnnotationMap = {1: true, 2: true}
      annotationUI.xorSelectedAnnotations([{id: 3}, {id: 4}])
      assert.deepEqual(annotationUI.selectedAnnotationMap, {
        1: true, 2: true, 3: true, 4: true
      })
    it 'removes annotations already in the selectedAnnotationMap', ->
      annotationUI.selectedAnnotationMap = {1: true, 2: true}
      annotationUI.xorSelectedAnnotations([{id: 1}, {id: 2}])
      assert.deepEqual(annotationUI.selectedAnnotationMap, {})

  describe '.removeSelectedAnnotation', ->
    it 'removes an annotation from the selectedAnnotationMap', ->
      annotationUI.selectedAnnotationMap = {1: true, 2: true, 3: true}
      annotationUI.removeSelectedAnnotation(id: 2)
      assert.deepEqual(annotationUI.selectedAnnotationMap, {
        1: true, 3: true
      })
