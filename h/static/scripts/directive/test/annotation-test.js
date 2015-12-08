/* jshint node: true */
'use strict';

var events = require('../../events');

var module = angular.mock.module;
var inject = angular.mock.inject;

/** Return Angular's $compile service. */
function compileService() {
  var $compile;
  inject(function(_$compile_) {
    $compile = _$compile_;
  });
  return $compile;
}

/** Return Angular's $document service. */
function documentService() {
  var $document;
  inject(function(_$document_) {
    $document = _$document_;
  });
  return $document;
}

describe('annotation.js', function() {

  describe('extractDocumentMetadata()', function() {
    var extractDocumentMetadata = require('../annotation')
                                    .extractDocumentMetadata;

    context('when the model has a document property', function() {
      it('returns the hostname from model.uri as the domain', function() {
        var model = {
          document: {},
          uri: 'http://example.com/'
        };

        assert.equal(extractDocumentMetadata(model).domain, 'example.com');
      });

      context('when model.uri starts with "urn"', function() {
        it(
          'uses the first document.link uri that doesn\'t start with "urn"',
          function() {
            var model = {
              uri: 'urn:isbn:0451450523',
              document: {
                link: [
                  {href: 'urn:isan:0000-0000-9E59-0000-O-0000-0000-2'},
                  {href: 'http://example.com/'}
                ]
              }
            };

            assert.equal(
              extractDocumentMetadata(model).uri, 'http://example.com/');
          }
        );
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

      context('when document.title is a string', function() {
        it('returns document.title as title', function() {
          var model = {
            uri: 'http://example.com/',
            document: {
              title: 'My Document'
            }
          };

          assert.equal(
            extractDocumentMetadata(model).title, model.document.title);
        });
      });

      context('when document.title is an array', function() {
        it('returns document.title[0] as title', function() {
          var model = {
            uri: 'http://example.com/',
            document: {
              title: ['My Document', 'My Other Document']
            }
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
            title: 'My Really Really Long Document Title'
          }
        };

        assert.equal(
          extractDocumentMetadata(model).title,
          'My Really Really Long Document…'
        );
      });
    });
  });

  describe('updateViewModel()', function() {
    var updateViewModel = require('../annotation').updateViewModel;
    var sandbox;

    beforeEach(function() {
      sandbox = sinon.sandbox.create();
    });

    afterEach(function() {
      sandbox.restore();
    });

    it('copies model.document.title to vm.document.title', function() {
      var vm = {};
      var model = {
        uri: 'http://example.com/example.html',
        document: {
          title: 'A special document'
        }
      };

      updateViewModel(model, vm);

      assert.equal(vm.document.title, 'A special document');
    });

    it('uses the first title when there are more than one', function() {
      var vm = {};
      var model = {
        uri: 'http://example.com/example.html',
        document: {
          title: ['first title', 'second title']
        }
      };

      updateViewModel(model, vm);

      assert.equal(vm.document.title, 'first title');
    });

    it('truncates long titles', function() {
      var vm = {};
      var model = {
        uri: 'http://example.com/example.html',
        document: {
          title: 'A very very very long title that really\nshouldn\'t be found on a page on the internet.'
        }
      };

      updateViewModel(model, vm);

      assert.equal(
        vm.document.title, 'A very very very long title th…');
    });

    it('copies model.uri to vm.document.uri', function() {
      var vm = {};
      var model = {
        uri: 'http://example.com/example.html',
      };

      updateViewModel(model, vm);

      assert.equal(vm.document.uri, 'http://example.com/example.html');
    });

    it('copies the hostname from model.uri to vm.document.domain', function() {
      var vm = {};
      var model = {
        uri: 'http://example.com/example.html',
      };

      updateViewModel(model, vm);

      assert.equal(vm.document.domain, 'example.com');
    });

    it('uses the domain for the title if the title is not present', function() {
      var vm = {};
      var model = {
        uri: 'http://example.com',
        document: {}
      };

      updateViewModel(model, vm);

      assert.equal(vm.document.title, 'example.com');
    });

    it(
      'still sets the uri correctly if the annotation has no document',
      function() {
        var vm = {};
        var model = {
          uri: 'http://example.com',
          document: undefined
        };

        updateViewModel(model, vm);

        assert(vm.document.uri === 'http://example.com');
      }
    );

    it(
      'still sets the domain correctly if the annotation has no document',
      function() {
        var vm = {};
        var model = {
          uri: 'http://example.com',
          document: undefined
        };

        updateViewModel(model, vm);

        assert(vm.document.domain === 'example.com');
      }
    );

    it(
      'uses the domain for the title when the annotation has no document',
      function() {
        var vm = {};
        var model = {
          uri: 'http://example.com',
          document: undefined
        };

        updateViewModel(model, vm);

        assert(vm.document.title === 'example.com');
      }
    );
  });

  describe('updateDomainModel()', function() {
    var updateDomainModel = require('../annotation').updateDomainModel;

    it('copies text from viewModel into domainModel', function() {
      var domainModel = {};
      var viewModel = {form: {text: 'bar', tags: []}};

      updateDomainModel(domainModel, viewModel);

      assert.equal(domainModel.text, viewModel.form.text);
    });

    it('overwrites text in domainModel', function() {
      var domainModel = {text: 'foo'};
      var viewModel = {form: {text: 'bar', tags: []}};

      updateDomainModel(domainModel, viewModel);

      assert.equal(domainModel.text, viewModel.form.text);
    });

    it('doesn\'t touch other properties in domainModel', function() {
      var domainModel = {foo: 'foo', bar: 'bar'};
      var viewModel = {form: {foo: 'FOO', tags: []}};

      updateDomainModel(domainModel, viewModel);

      assert.equal(
        domainModel.bar, 'bar',
        'updateDomainModel() should not touch properties of domainModel' +
        'that don\'t exist in viewModel');
    });

    it('copies tag texts from viewModel into domainModel', function() {
      var domainModel = {};
      var viewModel = {
        form: {
          tags: [
            {text: 'foo'},
            {text: 'bar'}
          ]
        }
      };

      updateDomainModel(domainModel, viewModel);

      assert.deepEqual(
        domainModel.tags, ['foo', 'bar'],
        'The array of {tag: "text"} objects in  viewModel becomes an array ' +
        'of "text" strings in domainModel');
    });
  });

  describe('validate()', function() {
    var validate = require('../annotation').validate;

    it('returns undefined if value is not an object', function() {
      var i;
      var values = [2, 'foo', true, null];
      for (i = 0; i < values.length; i++) {
        assert.equal(validate(values[i]));
      }
    });

    it(
      'returns the length if the value contains a non-empty tags array',
      function() {
        assert.equal(
          validate({
            tags: ['foo', 'bar'],
            permissions: {
              read: ['group:__world__']
            },
            target: [1, 2, 3]
          }),
          2);
      }
    );

    it(
      'returns the length if the value contains a non-empty text string',
      function() {
        assert.equal(
          validate({
            text: 'foobar',
            permissions: {
              read: ['group:__world__']
            },
            target: [1, 2, 3]
          }),
          6);
      }
    );

    it('returns true for private highlights', function() {
      assert.equal(
        validate({
          permissions: {
            read: ['acct:seanh@hypothes.is']
          },
          target: [1, 2, 3]
        }),
        true);
    });

    it('returns true for group highlights', function() {
      assert.equal(
        validate({
          permissions: {
            read: ['group:foo']
          },
          target: [1, 2, 3]
        }),
        true);
    });

    it('returns false for public highlights', function() {
      assert.equal(
        validate(
          {text: undefined, tags: undefined, target: [1, 2, 3],
           permissions: {read: ['group:__world__']}}
        ),
        false);
    });

    it('handles values with no permissions', function() {
      assert.equal(
        validate({
          permissions: void 0,
          target: [1, 2, 3]
        }),
        true);
    });

    it('handles permissions objects with no read', function() {
      assert.equal(
        validate({
          permissions: {
            read: void 0
          },
          target: [1, 2, 3]
        }),
        true);
    });
  });

  describe('AnnotationController', function() {
    var $q;
    var $rootScope;
    var $scope;
    var $timeout;
    var $window;
    var fakeAnnotationMapper;
    var fakeAnnotationUI;
    var fakeDocumentDomainFilter;
    var fakeDocumentTitleFilter;
    var fakeDrafts;
    var fakeFeatures;
    var fakeFlash;
    var fakeGroups;
    var fakeMomentFilter;
    var fakePermissions;
    var fakePersonaFilter;
    var fakeSession;
    var fakeTags;
    var fakeTime;
    var fakeUrlEncodeFilter;
    var sandbox;

    function createDirective(annotation) {
      annotation = annotation || defaultAnnotation();
      $scope.annotation = annotation;
      var element = angular.element('<div annotation="annotation">');
      compileService()(element)($scope);
      $scope.$digest();
      var controller = element.controller('annotation');
      var scope = element.isolateScope();
      return {
        annotation: annotation,
        controller: controller,
        element: element,
        scope: scope
      };
    }

    /** Return the default domain model object that createDirective() uses if
     *  no custom one is passed to it. */
    function defaultAnnotation() {
      return {
        id: 'deadbeef',
        document: {
          title: 'A special document'
        },
        target: [{}],
        uri: 'http://example.com',
        user: 'acct:bill@localhost'
      };
    }

    /** Return an annotation domain model object for a new annotation
     * (newly-created client-side, not yet saved to the server).
     */
    function newAnnotation() {
      // A new annotation won't have any saved drafts yet.
      fakeDrafts.get.returns(null);
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
      // A new highlight won't have any saved drafts yet.
      fakeDrafts.get.returns(null);
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

    before(function() {
      angular.module('h', [])
        .directive('annotation', require('../annotation').directive);
    });

    beforeEach(module('h'));

    beforeEach(module('h.templates'));

    beforeEach(module(function($provide) {
      sandbox = sinon.sandbox.create();

      fakeAnnotationMapper = {
        createAnnotation: sandbox.stub().returns({
          permissions: {
            read: ['acct:bill@localhost'],
            update: ['acct:bill@localhost'],
            destroy: ['acct:bill@localhost'],
            admin: ['acct:bill@localhost']
          }
        }),
        deleteAnnotation: sandbox.stub()
      };

      fakeAnnotationUI = {};

      fakeDrafts = {
        update: sandbox.stub(),
        remove: sandbox.stub(),
        get: sandbox.stub()
      };

      fakeFeatures = {
        flagEnabled: sandbox.stub().returns(true)
      };

      fakeFlash = sandbox.stub();

      fakeMomentFilter = sandbox.stub().returns('ages ago');

      fakePermissions = {
        isShared: sandbox.stub().returns(true),
        isPrivate: sandbox.stub().returns(false),
        permits: sandbox.stub().returns(true),
        shared: sandbox.stub().returns({
          read: ['everybody']
        }),
        'private': sandbox.stub().returns({
          read: ['justme']
        }),
        'default': sandbox.stub().returns({
          read: ['default']
        }),
        setDefault: sandbox.stub()
      };

      fakePersonaFilter = sandbox.stub().returnsArg(0);

      fakeDocumentTitleFilter = function(arg) {
        return '';
      };

      fakeDocumentDomainFilter = function(arg) {
        return '';
      };

      fakeSession = {
        state: {
          userid: 'acct:bill@localhost'
        }
      };

      fakeTags = {
        filter: sandbox.stub().returns('a while ago'),
        store: sandbox.stub()
      };

      fakeTime = {
        toFuzzyString: sandbox.stub().returns('a while ago'),
        nextFuzzyUpdate: sandbox.stub().returns(30)
      };

      fakeUrlEncodeFilter = function(v) {
        return encodeURIComponent(v);
      };

      fakeGroups = {
        focused: function() {
          return {};
        },
        get: function() {}
      };

      $provide.value('annotationMapper', fakeAnnotationMapper);
      $provide.value('annotationUI', fakeAnnotationUI);
      $provide.value('drafts', fakeDrafts);
      $provide.value('features', fakeFeatures);
      $provide.value('flash', fakeFlash);
      $provide.value('momentFilter', fakeMomentFilter);
      $provide.value('permissions', fakePermissions);
      $provide.value('personaFilter', fakePersonaFilter);
      $provide.value('documentTitleFilter', fakeDocumentTitleFilter);
      $provide.value('documentDomainFilter', fakeDocumentDomainFilter);
      $provide.value('session', fakeSession);
      $provide.value('tags', fakeTags);
      $provide.value('time', fakeTime);
      $provide.value('urlencodeFilter', fakeUrlEncodeFilter);
      $provide.value('groups', fakeGroups);
    }));

    beforeEach(
      inject(
        function(_$q_, _$rootScope_, _$timeout_,
                _$window_) {
          $window = _$window_;
          $q = _$q_;
          $timeout = _$timeout_;
          $rootScope = _$rootScope_;
          $scope = $rootScope.$new();
        }
      )
    );

    afterEach(function() {
      sandbox.restore();
    });

    describe('AnnotationController() initialization', function() {
      it('sets the user of annotations that don\'t have one', function() {
        // You can create annotations while logged out and then login.
        // When you login a new AnnotationController instance is created for
        // each of your annotations, and on initialization it will set the
        // annotation's user to your username from the session.
        var annotation = newAnnotation();
        annotation.user = undefined;
        fakeSession.state.userid = 'acct:bill@localhost';

        createDirective(annotation);

        assert.equal(annotation.user, 'acct:bill@localhost');
      });

      it(
        'sets the permissions of annotations that don\'t have any',
        function() {
          // You can create annotations while logged out and then login.
          // When you login a new AnnotationController instance is created for
          // each of your annotations, and on initialization it will set the
          // annotation's permissions using your username from the session.
          var annotation = newAnnotation();
          annotation.user = annotation.permissions = undefined;
          fakeSession.state.userid = 'acct:bill@localhost';
          fakePermissions.default.returns('default permissions');

          createDirective(annotation);

          assert.equal(annotation.permissions, 'default permissions');
        }
      );

      it('saves new highlights to the server on initialization', function() {
        var annotation = newHighlight();
        // The user is logged-in.
        annotation.user = fakeSession.state.userid = 'acct:bill@localhost';
        annotation.$create = sandbox.stub().returns({
          then: function() {}
        });

        createDirective(annotation);

        assert.called(annotation.$create);
      });

      it('saves new highlights to drafts if not logged in', function() {
        var annotation = newHighlight();
        // The user is not logged-in.
        annotation.user = fakeSession.state.userid = undefined;
        annotation.$create = sandbox.stub().returns({
          then: function() {}
        });

        createDirective(annotation);

        assert.notCalled(annotation.$create);
        assert.called(fakeDrafts.update);
      });

      it('does not save new annotations on initialization', function() {
        var annotation = newAnnotation();
        annotation.$create = sandbox.stub().returns({
          then: function() {}
        });

        createDirective(annotation);

        assert.notCalled(annotation.$create);
      });

      it('does not save old highlights on initialization', function() {
        var annotation = oldHighlight();
        annotation.$create = sandbox.stub().returns({
          then: function() {}
        });

        createDirective(annotation);

        assert.notCalled(annotation.$create);
      });

      it('does not save old annotations on initialization', function() {
        var annotation = oldAnnotation();
        annotation.$create = sandbox.stub().returns({
          then: function() {}
        });

        createDirective(annotation);

        assert.notCalled(annotation.$create);
      });

      it('edits new annotations on initialization', function() {
        var annotation = newAnnotation();

        var controller = createDirective(annotation).controller;

        assert.isTrue(controller.editing());
      });

      it('edits annotations with drafts on initialization', function() {
        var annotation = oldAnnotation();
        // The drafts service has some draft changes for this annotation.
        fakeDrafts.get.returns('foo');

        var controller = createDirective(annotation).controller;

        assert.isTrue(controller.editing());
      });

      it('does not edit new highlights on initialization', function() {
        var annotation = newHighlight();
        // We have to set annotation.$create() because it'll try to call it.
        annotation.$create = sandbox.stub().returns({
          then: function() {}
        });

        var controller = createDirective(annotation).controller;

        assert.isFalse(controller.editing());
      });

      it('edits highlights with drafts on initialization', function() {
        var annotation = oldHighlight();
        // You can edit a highlight, enter some text or tags, and save it (the
        // highlight then becomes an annotation). You can also edit a highlight
        // and then change focus to another group and back without saving the
        // highlight, in which case the highlight will have draft edits.
        // This highlight has draft edits.
        fakeDrafts.get.returns('foo');

        var controller = createDirective(annotation).controller;

        assert.isTrue(controller.editing());
      });
    });

    describe('AnnotationController.editing()', function() {
      it('returns true if action is "create"', function() {
        var controller = createDirective().controller;
        controller.action = 'create';
        assert(controller.editing());
      });

      it('returns true if action is "edit"', function() {
        var controller = createDirective().controller;
        controller.action = 'edit';
        assert(controller.editing());
      });

      it('returns false if action is "view"', function() {
        var controller = createDirective().controller;
        controller.action = 'view';
        assert(!controller.editing());
      });
    });

    describe('AnnotationController.isHighlight()', function() {
      it('returns true for new highlights', function() {
        var annotation = newHighlight();
        // We need to define $create because it'll try to call it.
        annotation.$create = function() {return {then: function() {}};};

        var vm = createDirective(annotation).controller;

        assert.isTrue(vm.isHighlight());
      });

      it('returns false for new annotations', function() {
        var annotation = newAnnotation();

        var vm = createDirective(annotation).controller;

        assert.isFalse(vm.isHighlight());
      });

      it('returns false for page notes', function() {
        var annotation = oldPageNote();

        var vm = createDirective(annotation).controller;

        assert.isFalse(vm.isHighlight());
      });

      it('returns false for replies', function() {
        var annotation = oldReply();

        var vm = createDirective(annotation).controller;

        assert.isFalse(vm.isHighlight());
      });

      it('returns false for annotations with text but no tags', function() {
        var annotation = oldAnnotation();
        annotation.text = 'This is my annotation';
        annotation.tags = [];

        var vm = createDirective(annotation).controller;

        assert.isFalse(vm.isHighlight());
      });

      it('returns false for annotations with tags but no text', function() {
        var annotation = oldAnnotation();
        annotation.text = '';
        annotation.tags = ['foo'];

        var vm = createDirective(annotation).controller;

        assert.isFalse(vm.isHighlight());
      });

      it('returns true for annotations with no text or tags', function() {
        var annotation = oldAnnotation();
        annotation.text = '';
        annotation.tags = [];

        var vm = createDirective(annotation).controller;

        assert.isTrue(vm.isHighlight());
      });
    });

    describe('when the annotation is a highlight', function() {
      var annotation;

      beforeEach(function() {
        annotation = defaultAnnotation();
        annotation.$highlight = true;
        annotation.$create = sinon.stub().returns({
          then: angular.noop,
          'catch': angular.noop,
          'finally': angular.noop
        });
      });

      it('is private', function() {
        delete annotation.id;
        createDirective(annotation);
        $scope.$digest();
        assert.deepEqual(annotation.permissions, {
          read: ['justme']
        });
      });
    });

    describe('#reply', function() {
      var annotation;

      beforeEach(function() {
        annotation = defaultAnnotation();
        annotation.permissions = {
          read: ['acct:joe@localhost'],
          update: ['acct:joe@localhost'],
          destroy: ['acct:joe@localhost'],
          admin: ['acct:joe@localhost']
        };
      });

      it('creates a new reply with the proper uri and references', function() {
        var controller = createDirective(annotation).controller;
        controller.reply();
        var match = sinon.match({
          references: [annotation.id],
          uri: annotation.uri
        });
        assert.calledWith(fakeAnnotationMapper.createAnnotation, match);
      });

      it('makes the annotation shared if the parent is shared', function() {
        var controller = createDirective(annotation).controller;
        var reply = {};
        fakeAnnotationMapper.createAnnotation.returns(reply);
        fakePermissions.isShared.returns(true);
        controller.reply();
        assert.deepEqual(reply.permissions, {
          read: ['everybody']
        });
      });

      it('makes the annotation shared if the parent is shared', function() {
        var controller = createDirective(annotation).controller;
        $scope.annotation.group = 'my group';
        $scope.annotation.permissions = {
          read: ['my group']
        };
        var reply = {};
        fakeAnnotationMapper.createAnnotation.returns(reply);
        fakePermissions.isShared = function(permissions, group) {
          return permissions.read.indexOf(group) !== -1;
        };
        fakePermissions.shared = function(group) {
          return {
            read: [group]
          };
        };
        controller.reply();
        assert(reply.permissions.read.indexOf('my group') !== -1);
      });

      it(
        'does not add the world readable principal if the parent is private',
        function() {
          var controller = createDirective(annotation).controller;
          var reply = {};
          fakeAnnotationMapper.createAnnotation.returns(reply);
          fakePermissions.isShared.returns(false);
          controller.reply();
          assert.deepEqual(reply.permissions, {
            read: ['justme']
          });
        }
      );

      it('sets the reply\'s group to be the same as its parent\'s', function() {
        var controller = createDirective(annotation).controller;
        $scope.annotation.group = 'my group';
        var reply = {};
        fakeAnnotationMapper.createAnnotation.returns(reply);
        controller.reply();
        assert.equal(reply.group, $scope.annotation.group);
      });
    });

    describe('#setPrivacy', function() {
      it('makes the annotation private when level is "private"', function() {
        var parts = createDirective();
        parts.annotation.$update = sinon.stub().returns(Promise.resolve());
        parts.controller.edit();
        parts.controller.setPrivacy('private');
        return parts.controller.save().then(function() {
          // Verify that the permissions are updated once the annotation
          // is saved.
          assert.deepEqual(parts.annotation.permissions, {
            read: ['justme']
          });
        });
      });

      it('makes the annotation shared when level is "shared"', function() {
        var parts = createDirective();
        parts.annotation.$update = sinon.stub().returns(Promise.resolve());
        parts.controller.edit();
        parts.controller.setPrivacy('shared');
        return parts.controller.save().then(function() {
          assert.deepEqual(parts.annotation.permissions, {
            read: ['everybody']
          });
        });
      });

      it('saves the "shared" visibility level to localStorage', function() {
        var parts = createDirective();
        parts.annotation.$update = sinon.stub().returns(Promise.resolve());
        parts.controller.edit();
        parts.controller.setPrivacy('shared');
        return parts.controller.save().then(function() {
          assert(fakePermissions.setDefault.calledWithExactly('shared'));
        });
      });

      it('saves the "private" visibility level to localStorage', function() {
        var parts = createDirective();
        parts.annotation.$update = sinon.stub().returns(Promise.resolve());
        parts.controller.edit();
        parts.controller.setPrivacy('private');
        return parts.controller.save().then(function() {
          assert(fakePermissions.setDefault.calledWithExactly('private'));
        });
      });

      it('doesn\'t save the visibility if the annotation is a reply', function() {
        var parts = createDirective();
        parts.annotation.$update = sinon.stub().returns(Promise.resolve());
        parts.annotation.references = ['parent id'];
        parts.controller.edit();
        parts.controller.setPrivacy('private');
        return parts.controller.save().then(function() {
          assert(!fakePermissions.setDefault.called);
        });
      });
    });

    describe('#hasContent', function() {
      it('returns false if the annotation has no tags or text', function() {
        var controller = createDirective().controller;
        controller.form.text = '';
        controller.form.tags = [];
        assert.ok(!controller.hasContent());
      });

      it('returns true if the annotation has tags or text', function() {
        var controller = createDirective().controller;
        controller.form.text = 'bar';
        assert.ok(controller.hasContent());
        controller.form.text = '';
        controller.form.tags = [
          {
            text: 'foo'
          }
        ];
        assert.ok(controller.hasContent());
      });
    });

    describe('#hasQuotes', function() {
      it('returns false if the annotation has no quotes', function() {
        var annotation = defaultAnnotation();
        annotation.target = [{}];
        var controller = createDirective(annotation).controller;

        assert.isFalse(controller.hasQuotes());
      });

      it('returns true if the annotation has quotes', function() {
        var annotation = defaultAnnotation();
        annotation.target = [
          {
            selector: [
              {
                type: 'TextQuoteSelector'
              }
            ]
          }
        ];
        var controller = createDirective(annotation).controller;

        assert.isTrue(controller.hasQuotes());
      });
    });

    describe('timestamp', function() {
      var annotation;
      var clock;

      beforeEach(function() {
        clock = sinon.useFakeTimers();
        annotation = defaultAnnotation();
        annotation.created = (new Date()).toString();
        annotation.updated = (new Date()).toString();
      });

      afterEach(function() {
        clock.restore();
      });

      it('is not updated for unsaved annotations', function() {
        annotation.updated = null;
        var controller = createDirective(annotation).controller;
        // Unsaved annotations don't have an updated time yet so a timestamp
        // string can't be computed for them.
        $scope.$digest();
        assert.equal(controller.timestamp, null);
      });

      it('is updated on first digest', function() {
        var controller = createDirective(annotation).controller;
        $scope.$digest();
        assert.equal(controller.timestamp, 'a while ago');
      });

      it('is updated after a timeout', function() {
        var controller = createDirective(annotation).controller;
        fakeTime.nextFuzzyUpdate.returns(10);
        fakeTime.toFuzzyString.returns('ages ago');
        $scope.$digest();
        clock.tick(11000);
        $timeout.flush();
        assert.equal(controller.timestamp, 'ages ago');
      });

      it('is no longer updated after the scope is destroyed', function() {
        var controller = createDirective(annotation).controller;
        $scope.$digest();
        $scope.$destroy();
        $timeout.flush();
        $timeout.verifyNoPendingTasks();
      });
    });

    describe('share', function() {
      it('sets and unsets the open class on the share wrapper', function() {
        var parts = createDirective();
        var dialog = parts.element.find('.share-dialog-wrapper');
        dialog.find('button').click();
        parts.scope.$digest();
        assert.ok(dialog.hasClass('open'));
        documentService().click();
        assert.notOk(dialog.hasClass('open'));
      });
    });

    describe('deleteAnnotation() method', function() {
      beforeEach(function() {
        fakeAnnotationMapper.deleteAnnotation = sandbox.stub();
        fakeFlash.error = sandbox.stub();
      });

      it(
        'calls annotationMapper.delete() if the delete is confirmed',
        function(done) {
          var parts = createDirective();
          sandbox.stub($window, 'confirm').returns(true);
          fakeAnnotationMapper.deleteAnnotation.returns($q.resolve());
          parts.controller['delete']().then(function() {
            assert(
              fakeAnnotationMapper.deleteAnnotation.calledWith(
                parts.annotation));
            done();
          });
          $timeout.flush();
        }
      );

      it(
        'doesn\'t call annotationMapper.delete() if the delete is cancelled',
        function() {
          var controller = createDirective().controller;
          sandbox.stub($window, 'confirm').returns(false);
          assert(fakeAnnotationMapper.deleteAnnotation.notCalled);
        }
      );

      it(
        'flashes a generic error if the server cannot be reached',
        function(done) {
          var controller = createDirective().controller;
          sandbox.stub($window, 'confirm').returns(true);
          fakeAnnotationMapper.deleteAnnotation.returns($q.reject({
            status: 0
          }));
          controller['delete']().then(function() {
            assert(fakeFlash.error.calledWith(
              'Service unreachable.', 'Deleting annotation failed'));
            done();
          });
          $timeout.flush();
        }
      );

      it('flashes an error if the delete fails on the server', function(done) {
        var controller = createDirective().controller;
        sandbox.stub($window, 'confirm').returns(true);
        fakeAnnotationMapper.deleteAnnotation.returns($q.reject({
          status: 500,
          statusText: 'Server Error',
          data: {}
        }));
        controller['delete']().then(function() {
          assert(fakeFlash.error.calledWith(
            '500 Server Error', 'Deleting annotation failed'));
          done();
        });
        $timeout.flush();
      });

      it('doesn\'t flash an error if the delete succeeds', function(done) {
        var controller = createDirective().controller;
        sandbox.stub($window, 'confirm').returns(true);
        fakeAnnotationMapper.deleteAnnotation.returns($q.resolve());
        controller['delete']().then(function() {
          assert(fakeFlash.error.notCalled);
          done();
        });
        $timeout.flush();
      });
    });

    describe('saving a new annotation', function() {
      var annotation;

      beforeEach(function() {
        fakeFlash.error = sandbox.stub();
        annotation = defaultAnnotation();
        annotation.$create = sandbox.stub();
      });

      function controllerWithActionCreate() {
        var controller = createDirective(annotation).controller;
        controller.action = 'create';
        return controller;
      }

      it(
        'emits annotationCreated when saving an annotation succeeds',
        function(done) {
          var controller = controllerWithActionCreate();
          sandbox.spy($rootScope, '$emit');
          annotation.$create.returns(Promise.resolve());
          controller.save().then(function() {
            assert($rootScope.$emit.calledWith('annotationCreated'));
            done();
          });
        }
      );

      it(
        'flashes a generic error if the server can\'t be reached',
        function(done) {
          var controller = controllerWithActionCreate();
          annotation.$create.returns(Promise.reject({
            status: 0
          }));
          controller.save().then(function() {
            assert(fakeFlash.error.calledWith(
              'Service unreachable.', 'Saving annotation failed'));
            done();
          });
        }
      );

      it(
        'flashes an error if saving the annotation fails on the server',
        function(done) {
          var controller = controllerWithActionCreate();
          annotation.$create.returns(Promise.reject({
            status: 500,
            statusText: 'Server Error',
            data: {}
          }));
          controller.save().then(function() {
            assert(fakeFlash.error.calledWith(
              '500 Server Error', 'Saving annotation failed'));
            done();
          });
        }
      );

      it(
        'doesn\'t flash an error when saving an annotation succeeds',
        function() {
          var controller = controllerWithActionCreate();
          annotation.$create.returns(Promise.resolve());
          controller.save();
          assert(fakeFlash.error.notCalled);
        }
      );
    });

    describe('saving an edited an annotation', function() {
      var annotation;

      beforeEach(function() {
        fakeFlash.error = sandbox.stub();
        annotation = defaultAnnotation();
        annotation.$update = sandbox.stub();
      });

      function controllerWithActionEdit() {
        var controller = createDirective(annotation).controller;
        controller.action = 'edit';
        return controller;
      }

      it(
        'flashes a generic error if the server cannot be reached',
        function(done) {
          var controller = controllerWithActionEdit();
          annotation.$update.returns(Promise.reject({
            status: 0
          }));
          controller.save().then(function() {
            assert(fakeFlash.error.calledWith(
              'Service unreachable.', 'Saving annotation failed'));
            done();
          });
        }
      );

      it(
        'flashes an error if saving the annotation fails on the server',
        function(done) {
          var controller = controllerWithActionEdit();
          annotation.$update.returns(Promise.reject({
            status: 500,
            statusText: 'Server Error',
            data: {}
          }));
          controller.save().then(function() {
            assert(fakeFlash.error.calledWith(
              '500 Server Error', 'Saving annotation failed'));
            done();
          });
        }
      );

      it(
        'doesn\'t flash an error if saving the annotation succeeds',
        function() {
          var controller = controllerWithActionEdit();
          annotation.$update.returns(Promise.resolve());
          controller.save();
          assert(fakeFlash.error.notCalled);
        }
      );
    });

    describe('drafts', function() {
      it('creates a draft when editing an annotation', function() {
        var parts = createDirective();
        parts.controller.edit();
        assert.calledWith(fakeDrafts.update, parts.annotation);
      });

      it('starts editing immediately if there is a draft', function() {
        fakeDrafts.get.returns({
          tags: [
            {
              text: 'unsaved'
            }
          ],
          text: 'unsaved-text'
        });
        var controller = createDirective().controller;
        assert.isTrue(controller.editing());
      });

      it('uses the text and tags from the draft if present', function() {
        fakeDrafts.get.returns({
          tags: ['unsaved-tag'],
          text: 'unsaved-text'
        });
        var controller = createDirective().controller;
        assert.deepEqual(controller.form.tags, [
          {
            text: 'unsaved-tag'
          }
        ]);
        assert.equal(controller.form.text, 'unsaved-text');
      });

      it('removes the draft when changes are discarded', function() {
        var parts = createDirective();
        parts.controller.edit();
        parts.controller.revert();
        assert.calledWith(fakeDrafts.remove, parts.annotation);
      });

      it('removes the draft when changes are saved', function() {
        var annotation = defaultAnnotation();
        annotation.$update = sandbox.stub().returns(Promise.resolve());
        var controller = createDirective(annotation).controller;
        controller.edit();
        return controller.save().then(function() {
          assert.calledWith(fakeDrafts.remove, annotation);
        });
      });
    });

    describe('when the focused group changes', function() {
      it('updates the current draft', function() {
        var parts = createDirective();
        parts.controller.edit();
        parts.controller.form.text = 'unsaved-text';
        parts.controller.form.tags = [];
        fakeDrafts.get = sinon.stub().returns({
          text: 'old-draft'
        });
        fakeDrafts.update = sinon.stub();
        fakePermissions.isPrivate.returns(true);

        $rootScope.$broadcast(events.GROUP_FOCUSED);

        assert.calledWith(
          fakeDrafts.update,
          parts.annotation, true, [], 'unsaved-text');
      });

      it('should not create a new draft', function() {
        var controller = createDirective().controller;
        controller.edit();
        fakeDrafts.update = sinon.stub();
        fakeDrafts.get = sinon.stub().returns(null);
        $rootScope.$broadcast(events.GROUP_FOCUSED);
        assert.notCalled(fakeDrafts.update);
      });

      it('moves new annotations to the focused group', function() {
        var annotation = defaultAnnotation();
        // id must be null so that AnnotationController considers this a new
        // annotation.
        annotation.id = null;
        var controller = createDirective(annotation).controller;
        fakeGroups.get = sandbox.stub().returns({id: 'new-group'});

        // Change the currently focused group.
        fakeGroups.focused = sinon.stub().returns({id: 'new-group'});
        $rootScope.$broadcast(events.GROUP_FOCUSED);

        var group = controller.group().id;

        assert.isTrue(fakeGroups.get.calledOnce);
        assert.isTrue(fakeGroups.get.calledWithExactly('new-group'));
        assert.equal(
          group, 'new-group',
          'It should update the group ID in the view model when the focused ' +
          'group changes.');
      });
    });

    it(
      'updates perms when moving new annotations to the focused group',
      function() {
        var annotation = defaultAnnotation();
        // id must be null so that AnnotationController considers this a new
        // annotation.
        annotation.id = null;
        annotation.group = 'old-group';
        annotation.permissions = {read: [annotation.group]};
        // This is a shared annotation.
        fakePermissions.isShared.returns(true);
        createDirective(annotation);
        // Make permissions.shared() behave like we expect it to.
        fakePermissions.shared = function(groupId) {
          return {
            read: [groupId]
          };
        };

        // Change the currently focused group.
        fakeGroups.focused = sinon.stub().returns({id: 'new-group'});
        $rootScope.$broadcast(events.GROUP_FOCUSED);

        assert.deepEqual(annotation.permissions.read, ['new-group']);
      }
    );

    it('does not change perms when moving new private annotations', function() {
      // id must be null so that AnnotationController considers this a new
      // annotation.
      var annotation = defaultAnnotation();
      annotation.id = null;
      annotation.group = 'old-group';
      annotation.permissions = {
        read: ['acct:bill@localhost']
      };
      createDirective(annotation);
      // This is a private annotation.
      fakePermissions.isShared.returns(false);
      fakeGroups.focused = sinon.stub().returns({
        id: 'new-group'
      });
      $rootScope.$broadcast(events.GROUP_FOCUSED);
      assert.deepEqual(
        annotation.permissions.read, ['acct:bill@localhost'],
        'The annotation should still be private');
    });
  });

  describe('AnnotationController', function() {
    before(function() {
      angular.module('h', [])
        .directive('annotation', require('../annotation').directive);
    });

    beforeEach(module('h'));

    beforeEach(module('h.templates'));

    /** Return Angular's $rootScope. */
    function getRootScope() {
      var $rootScope;
      inject(function(_$rootScope_) {
        $rootScope = _$rootScope_;
      });
      return $rootScope;
    }

    /**
    Return an annotation directive instance and stub services etc.
    */
    function createAnnotationDirective(args) {
      var session = args.session || {
        state: {
          userid: 'acct:fred@hypothes.is'
        }
      };
      var locals = {
        personaFilter: args.personaFilter || function() {},
        momentFilter: args.momentFilter || {},
        urlencodeFilter: args.urlencodeFilter || {},
        drafts: args.drafts || {
          update: function() {},
          remove: function() {},
          get: function() {}
        },
        features: args.features || {
          flagEnabled: function() {
            return true;
          }
        },
        flash: args.flash || {
          info: function() {},
          error: function() {}
        },
        permissions: args.permissions || {
          isShared: function(permissions, group) {
            if (permissions.read) {
              return permissions.read.indexOf(group) !== -1;
            } else {
              return false;
            }
          },
          isPrivate: function(permissions, user) {
            if (permissions.read) {
              return permissions.read.indexOf(user) !== -1;
            } else {
              return false;
            }
          },
          permits: function() {
            return true;
          },
          shared: function() {
            return {};
          },
          'private': function() {
            return {};
          },
          'default': function() {
            return {};
          },
          setDefault: function() {}
        },
        session: session,
        tags: args.tags || {
          store: function() {}
        },
        time: args.time || {
          toFuzzyString: function() {},
          nextFuzzyUpdate: function() {}
        },
        annotationUI: args.annotationUI || {},
        annotationMapper: args.annotationMapper || {},
        groups: args.groups || {
          get: function() {},
          focused: function() {
            return {};
          }
        },
        documentTitleFilter: args.documentTitleFilter || function() {
          return '';
        },
        documentDomainFilter: args.documentDomainFilter || function() {
          return '';
        },
        localStorage: args.localStorage || {
          setItem: function() {},
          getItem: function() {}
        }
      };
      module(function($provide) {
        $provide.value('personaFilter', locals.personaFilter);
        $provide.value('momentFilter', locals.momentFilter);
        $provide.value('urlencodeFilter', locals.urlencodeFilter);
        $provide.value('drafts', locals.drafts);
        $provide.value('features', locals.features);
        $provide.value('flash', locals.flash);
        $provide.value('permissions', locals.permissions);
        $provide.value('session', locals.session);
        $provide.value('tags', locals.tags);
        $provide.value('time', locals.time);
        $provide.value('annotationUI', locals.annotationUI);
        $provide.value('annotationMapper', locals.annotationMapper);
        $provide.value('groups', locals.groups);
        $provide.value('documentTitleFilter', locals.documentTitleFilter);
        $provide.value('documentDomainFilter', locals.documentDomainFilter);
        $provide.value('localStorage', locals.localStorage);
      });
      locals.element = angular.element('<div annotation="annotation">');
      var compiledElement = compileService()(locals.element);
      locals.$rootScope = getRootScope();
      locals.parentScope = locals.$rootScope.$new();
      locals.parentScope.annotation = args.annotation || {};
      locals.directive = compiledElement(locals.parentScope);
      locals.$rootScope.$digest();
      locals.controller = locals.element.controller('annotation');
      locals.isolateScope = locals.element.isolateScope();
      return locals;
    }

    describe('createAnnotationDirective', function() {
      it('creates the directive without crashing', function() {
        createAnnotationDirective({});
      });
    });

    it('sets the user of new annotations', function() {
      var annotation = {};
      var session = createAnnotationDirective({
        annotation: annotation
      }).session;
      assert.equal(annotation.user, session.state.userid);
    });

    it('sets the permissions of new annotations', function() {
      // This is a new annotation, doesn't have any permissions yet.
      var annotation = {
        group: 'test-group'
      };
      var permissions = {
        'default': sinon.stub().returns('default permissions'),
        isShared: function() {},
        isPrivate: function() {}
      };
      createAnnotationDirective({
        annotation: annotation,
        permissions: permissions
      });
      assert(permissions['default'].calledWithExactly('test-group'));
      assert.equal(
        annotation.permissions, 'default permissions',
        'It should set a new annotation\'s permissions to what ' +
        'permissions.default() returns');
    });

    it(
      'doesn\'t overwrite permissions if the annotation already has them',
      function() {
        var annotation = {
          permissions: {
            read: ['foo'],
            update: ['bar'],
            'delete': ['gar'],
            admin: ['har']
          }
        };
        var originalPermissions = JSON.parse(JSON.stringify(
          annotation.permissions));
        var permissions = {
          'default': sinon.stub().returns('new permissions'),
          isShared: function() {},
          isPrivate: function() {}
        };
        createAnnotationDirective({
          annotation: annotation,
          permissions: permissions
        });
        assert.deepEqual(annotation.permissions, originalPermissions);
      }
    );

    describe('save', function() {
      it(
        'Passes group:<id> to the server when saving a new annotation',
        function() {
          var annotation = {
            user: 'acct:fred@hypothes.is',
            text: 'foo'
          };
          annotation.$create = sinon.stub().returns(Promise.resolve());
          var group = {
            id: 'test-id'
          };
          var controller = createAnnotationDirective({
            annotation: annotation,
            groups: {
              focused: function() {
                return group;
              },
              get: function() {}
            }
          }).controller;
          controller.action = 'create';
          return controller.save().then(function() {
            assert(annotation.$create.lastCall.thisValue.group === 'test-id');
          });
        }
      );
    });

    /*
    Simulate what happens when the user edits an annotation, clicks Save,
    gets an error because the server fails to save the annotation, then clicks
    Cancel - in the frontend the annotation should be restored to its original
    value, the edits lost.
      */
    it('restores the original text when editing is cancelled', function() {
      var controller = createAnnotationDirective({
        annotation: {
          id: 'test-annotation-id',
          user: 'acct:bill@localhost',
          text: 'Initial annotation body text',
          // Allow the initial save of the annotation to succeed.
          $create: function() {
            return Promise.resolve();
          },
          // Simulate saving the edit of the annotation to the server failing.
          $update: function() {
            return Promise.reject({
              status: 500,
              statusText: 'Server Error',
              data: {}
            });
          }
        }
      }).controller;
      var originalText = controller.form.text;
      // Simulate the user clicking the Edit button on the annotation.
      controller.edit();
      // Simulate the user typing some text into the annotation editor textarea.
      controller.form.text = 'changed by test code';
      // Simulate the user hitting the Save button and wait for the
      // (unsuccessful) response from the server.
      controller.save();
      // At this point the annotation editor controls are still open, and the
      // annotation's text is still the modified (unsaved) text.
      assert(controller.form.text === 'changed by test code');
      // Simulate the user clicking the Cancel button.
      controller.revert();
      assert(controller.form.text === originalText);
    });

    // test that editing reverting changes to an annotation with
    // no text resets the text to be empty.
    it('clears the text when reverting changes to a highlight', function() {
      var controller = createAnnotationDirective({
        annotation: {
          id: 'test-annotation-id',
          user: 'acct:bill@localhost'
        }
      }).controller;
      controller.edit();
      assert.equal(controller.action, 'edit');
      controller.form.text = 'this should be reverted';
      controller.revert();
      assert.equal(controller.form.text, void 0);
    });
  });
});
