'use strict';

var annotationMetadata = require('../annotation-metadata');

var extractDocumentMetadata = annotationMetadata.extractDocumentMetadata;

describe('annotation-metadata', function () {
  describe('.extractDocumentMetadata', function() {

    context('when the model has a document property', function() {
      it('returns the hostname from model.uri as the domain', function() {
        var model = {
          document: {},
          uri: 'http://example.com/'
        };

        assert.equal(extractDocumentMetadata(model).domain, 'example.com');
      });

      context('when model.uri does not start with "urn"', function() {
        it('uses model.uri as the uri', function() {
          var model = {
            document: {},
            uri: 'http://example.com/'
          };

          assert.equal(
            extractDocumentMetadata(model).uri, 'http://example.com/');
        });
      });

      context('when document.title is an available', function() {
        it('uses the first document title as the title', function() {
          var model = {
            uri: 'http://example.com/',
            document: {
              title: ['My Document', 'My Other Document']
            },
          };

          assert.equal(
            extractDocumentMetadata(model).title, model.document.title[0]);
        });
      });

      context('when there is no document.title', function() {
        it('returns the domain as the title', function() {
          var model = {
            document: {},
            uri: 'http://example.com/',
          };

          assert.equal(extractDocumentMetadata(model).title, 'example.com');
        });
      });
    });

    context('when the model does not have a document property', function() {
      it('returns model.uri for the uri', function() {
        var model = {uri: 'http://example.com/'};

        assert.equal(extractDocumentMetadata(model).uri, model.uri);
      });

      it('returns the hostname of model.uri for the domain', function() {
        var model = {uri: 'http://example.com/'};

        assert.equal(extractDocumentMetadata(model).domain, 'example.com');
      });

      it('returns the hostname of model.uri for the title', function() {
        var model = {uri: 'http://example.com/'};

        assert.equal(extractDocumentMetadata(model).title, 'example.com');
      });
    });

    context('when the title is longer than 30 characters', function() {
      it('truncates the title with "…"', function() {
        var model = {
          uri: 'http://example.com/',
          document: {
            title: ['My Really Really Long Document Title'],
          },
        };

        assert.equal(
          extractDocumentMetadata(model).title,
          'My Really Really Long Document…'
        );
      });
    });
  });

  describe('.location', function () {
    it('returns the position for annotations with a text position', function () {
      assert.equal(annotationMetadata.location({
        target: [{
          selector: [{
            type: 'TextPositionSelector',
            start: 100,
          }]
        }]
      }), 100);
    });

    it('returns +ve infinity for annotations without a text position', function () {
      assert.equal(annotationMetadata.location({
        target: [{
          selector: undefined,
        }]
      }), Number.POSITIVE_INFINITY);
    });
  });

  describe('.isPageNote', function () {
    it ('returns true for an annotation with an empty target', function () {
      assert.isTrue(annotationMetadata.isPageNote({
        target: []
      }));
    });
    it ('returns true for an annotation without selectors', function () {
      assert.isTrue(annotationMetadata.isPageNote({
        target: [{selector: undefined}]
      }));
    });
    it ('returns true for an annotation without a target', function () {
      assert.isTrue(annotationMetadata.isPageNote({
        target: undefined
      }));
    });
    it ('returns false for an annotation which is a reply', function () {
      assert.isFalse(annotationMetadata.isPageNote({
        target: [],
        references: ['xyz']
      }));
    });
  });

  describe ('.isAnnotation', function () {
    it ('returns true if an annotation is a top level annotation', function () {
      assert(annotationMetadata.isAnnotation({
        target: [{selector: []}]
      }));
    });
    it ('returns false if an annotation has no target', function () {
      assert.equal(annotationMetadata.isAnnotation({}), undefined);
    });
  });
});
