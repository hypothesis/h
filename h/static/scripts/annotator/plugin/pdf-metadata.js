'use strict';

/**
 * This PDFMetadata service extracts metadata about a loading/loaded PDF
 * document from a PDF.js PDFViewerApplication object.
 *
 * This hides from users of this service the need to wait until the PDF document
 * is loaded before extracting the relevant metadata.
 */
function PDFMetadata(app) {
  this._loaded = new Promise(function (resolve) {
    var finish = function () {
      window.removeEventListener('documentload', finish);
      resolve(app);
    };

    if (app.documentFingerprint) {
      resolve(app);
    } else {
      window.addEventListener('documentload', finish);
    }
  });
}

/**
 * Returns a promise of the URI of the loaded PDF.
 */
PDFMetadata.prototype.getUri = function () {
  return this._loaded.then(function (app) {
    return app.url;
  });
};

/**
 * Returns a promise of a metadata object, containing:
 *
 * title(string) - The document title
 * link(array) - An array of link objects representing URIs for the document
 * documentFingerprint(string) - The document fingerprint
 */
PDFMetadata.prototype.getMetadata = function () {
  return this._loaded.then(function (app) {
    var title = document.title;

    if (app.metadata && app.metadata.has('dc:title') && app.metadata.get('dc:title') !== 'Untitled') {
      title = app.metadata.get('dc:title');
    } else if (app.documentInfo && app.documentInfo.Title) {
      title = app.documentInfo.Title;
    }

    var link = [
      {href: fingerprintToURN(app.documentFingerprint)},
      {href: app.url}
    ];

    return {
      title: title,
      link: link,
      documentFingerprint: app.documentFingerprint,
    };
  });
};

function fingerprintToURN(fingerprint) {
  return 'urn:x-pdf:' + String(fingerprint);
}

module.exports = PDFMetadata;
