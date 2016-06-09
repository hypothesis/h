'use strict';

var PDFMetadata = require('../pdf-metadata');

describe('pdf-metadata', function () {
  describe('get pdf metadata when documentload event fires', function () {
    it('should get pdf urn', function () {
      var fakeApp = {};
      var pdfMetadata = new PDFMetadata(fakeApp);

      var event = document.createEvent('Event');
      event.initEvent('documentload', false, false);
      fakeApp.documentFingerprint = 'fakeFingerprint';
      window.dispatchEvent(event);

      return pdfMetadata.getUri().then(function (uri) {
        assert.equal('urn:x-pdf:fakeFingerprint', uri);
      });
    });
  });

  describe('get pdf metadata when documentFingerprint is set', function () {
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
          assert.equal('urn:x-pdf:fakeFingerprint', uri);
        });
      });
    });

    describe('#getMetadata', function () {
      it('should get a metadataobject with dc:title', function () {
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

      it('should get a metadataobject with documentInfo.Title', function () {
        var expectedMetadata = {
          title: fakePDFViewerApplication.documentInfo.Title,
          link: [{href: 'urn:x-pdf:' + fakePDFViewerApplication.documentFingerprint},
            {href: fakePDFViewerApplication.url}],
          documentFingerprint: fakePDFViewerApplication.documentFingerprint,
        };

        fakePDFViewerApplication.metadata.has = sinon.stub().returns(false);

        return pdfMetadata.getMetadata().then(function (actualMetadata) {
          assert.deepEqual(expectedMetadata, actualMetadata);
        });
      });
    });
  });
});
