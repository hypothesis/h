'use strict';

/**
 * Utility functions for querying annotation metadata.
 */

/** Extract a URI, domain and title from the given domain model object.
 *
 * @param {object} annotation An annotation domain model object as received
 *   from the server-side API.
 * @returns {object} An object with three properties extracted from the model:
 *   uri, domain and title.
 *
 */
function extractDocumentMetadata(annotation) {
  var uri = annotation.uri;
  var domain = new URL(uri).hostname;
  var title = domain;

  if (annotation.document && annotation.document.title) {
    title = annotation.document.title[0];
  }

  if (title.length > 30) {
    title = title.slice(0, 30) + '…';
  }

  return {
    uri: uri,
    domain: domain,
    title: title,
  };
}

/** Return `true` if the given annotation is a reply, `false` otherwise. */
function isReply(annotation) {
  return (annotation.references || []).length > 0;
}

/** Return `true` if the given annotation is new, `false` otherwise.
 *
 * "New" means this annotation has been newly created client-side and not
 * saved to the server yet.
 */
function isNew(annotation) {
  return !annotation.id;
}

/** Return a numeric key that can be used to sort annotations by location.
 *
 * @return {number} - A key representing the location of the annotation in
 *                    the document, where lower numbers mean closer to the
 *                    start.
 */
 function location(annotation) {
   if (annotation) {
     var targets = annotation.target || [];
     for (var i=0; i < targets.length; i++) {
       var selectors = targets[i].selector || [];
       for (var k=0; k < selectors.length; k++) {
         if (selectors[k].type === 'TextPositionSelector') {
           return selectors[k].start;
         }
       }
     }
   }
   return Number.POSITIVE_INFINITY;
 }

module.exports = {
  extractDocumentMetadata: extractDocumentMetadata,
  isReply: isReply,
  isNew: isNew,
  location: location,
};
