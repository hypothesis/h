/**
 * Return a fake annotation with the basic properties filled in.
 */
function defaultAnnotation() {
  return {
    id: 'deadbeef',
    document: {
      title: 'A special document'
    },
    target: [{}],
    uri: 'http://example.com',
    user: 'acct:bill@localhost',
    updated: '2015-05-10T20:18:56.613388+00:00',
  };
}

/** Return an annotation domain model object for a new annotation
 * (newly-created client-side, not yet saved to the server).
 */
function newAnnotation() {
  return {
    id: undefined,
    $highlight: undefined,
    target: ['foo', 'bar'],
    references: [],
    text: 'Annotation text',
    tags: ['tag_1', 'tag_2']
  };
}

/** Return an annotation domain model object for a new highlight
 * (newly-created client-side, not yet saved to the server).
 */
function newHighlight() {
  return {
    id: undefined,
    $highlight: true
  };
}

/** Return an annotation domain model object for an existing annotation
 *  received from the server.
 */
function oldAnnotation() {
  return {
    id: 'annotation_id',
    $highlight: undefined,
    target: ['foo', 'bar'],
    references: [],
    text: 'This is my annotation',
    tags: ['tag_1', 'tag_2']
  };
}

/** Return an annotation domain model object for an existing highlight
 *  received from the server.
 */
function oldHighlight() {
  return {
    id: 'annotation_id',
    $highlight: undefined,
    target: ['foo', 'bar'],
    references: [],
    text: '',
    tags: []
  };
}

/** Return an annotation domain model object for an existing page note
 *  received from the server.
 */
function oldPageNote() {
  return {
    highlight: undefined,
    target: [],
    references: [],
    text: '',
    tags: []
  };
}

/** Return an annotation domain model object for an existing reply
 *  received from the server.
 */
function oldReply() {
  return {
    highlight: undefined,
    target: ['foo'],
    references: ['parent_annotation_id'],
    text: '',
    tags: []
  };
}

module.exports = {
  defaultAnnotation: defaultAnnotation,
  newAnnotation: newAnnotation,
  newHighlight: newHighlight,
  oldAnnotation: oldAnnotation,
  oldHighlight: oldHighlight,
  oldPageNote: oldPageNote,
  oldReply: oldReply,
};
