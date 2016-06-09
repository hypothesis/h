'use strict';

var PDFMetadata = require('../pdf-metadata');

describe('pdf-metadata', function () {
  it('waits for the PDF to load before returning metadata', function () {
    var fakeApp = {};
    var pdfMetadata = new PDFMetadata(fakeApp);

    var event = document.createEvent('Event');
    event.initEvent('documentload', false, false);
    fakeApp.documentFingerprint = 'fakeFingerprint';
    window.dispatchEvent(event);

    return pdfMetadata.getUri().then(function (uri) {
      assert.equal(uri, 'urn:x-pdf:fakeFingerprint');
    });
  });

  it('does not wait for the PDF to load if it has already loaded', function () {
    var fakePDFViewerApplication = {documentFingerprint: 'fakeFingerprint'};
    var pdfMetadata = new PDFMetadata(fakePDFViewerApplication);
    return pdfMetadata.getUri().then(function (uri) {
      assert.equal(uri, 'urn:x-pdf:fakeFingerprint');
    });
  });

  describe('metadata sources', function () {
    var pdfMetadata;
    var fakePDFViewerApplication = {
      documentFingerprint: 'fakeFingerprint',
      documentInfo: {
        Title: 'fakeTitle',
      },
      metadata: {
        metadata: {
          'dc:title': 'fakeTitle',
        }
      },
      url: 'fakeUrl',
    };

    beforeEach(function () {
      pdfMetadata = new PDFMetadata(fakePDFViewerApplication);
    });

    describe('#getUri', function () {
      it('returns the URN-ified document fingerprint as its URI', function () {
        return pdfMetadata.getUri().then(function (uri) {
          assert.equal(uri, 'urn:x-pdf:fakeFingerprint');
        });
      });
    });

    describe('#getMetadata', function () {
      it('gets the title from the dc:title field', function () {
        var expectedMetadata = {
          title: 'dcTitle',
          link: [{href: 'urn:x-pdf:' + fakePDFViewerApplication.documentFingerprint},
            {href: fakePDFViewerApplication.url}],
          documentFingerprint: fakePDFViewerApplication.documentFingerprint,
        };

        fakePDFViewerApplication.metadata.has = sinon.stub().returns(true);
        fakePDFViewerApplication.metadata.get = sinon.stub().returns('dcTitle');

        return pdfMetadata.getMetadata().then(function (actualMetadata) {
          assert.deepEqual(expectedMetadata, actualMetadata);
        });
      });

      it('gets the title from the documentInfo.Title field', function () {
        var expectedMetadata = {
          title: fakePDFViewerApplication.documentInfo.Title,
          link: [{href: 'urn:x-pdf:' + fakePDFViewerApplication.documentFingerprint},
            {href: fakePDFViewerApplication.url}],
          documentFingerprint: fakePDFViewerApplication.documentFingerprint,
        };

        fakePDFViewerApplication.metadata.has = sinon.stub().returns(false);

        return pdfMetadata.getMetadata().then(function (actualMetadata) {
          assert.deepEqual(actualMetadata, expectedMetadata);
        });
      });
    });
  });
});
