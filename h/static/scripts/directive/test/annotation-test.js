/* jshint node: true */
'use strict';

var Promise = require('core-js/library/es6/promise');
var proxyquire = require('proxyquire');

var events = require('../../events');
var util = require('./util');

var module = angular.mock.module;
var inject = angular.mock.inject;

/**
 * Returns the annotation directive with helpers stubbed out.
 */
function annotationDirective() {
  var noop = function () { return '' };

  var annotation = proxyquire('../annotation', {
    '../filter/document-domain': noop,
    '../filter/document-title': noop,
    '../filter/persona': {
      username: noop,
    }
  });

  return annotation.directive;
}

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

describe('annotation', function() {

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

  describe('updateDomainModel()', function() {
    var updateDomainModel = require('../annotation').updateDomainModel;

    function fakePermissions() {
      return {
        shared: function() {},
        private: function() {},
      };
    }

    function fakeGroups() {
      return {
        focused: function() {return {};},
      };
    }

    it('copies text from viewModel into domainModel', function() {
      var domainModel = {};
      var viewModel = {form: {text: 'bar', tags: []}};

      updateDomainModel(domainModel, viewModel, fakePermissions(),
                        fakeGroups());

      assert.equal(domainModel.text, viewModel.form.text);
    });

    it('overwrites text in domainModel', function() {
      var domainModel = {text: 'foo'};
      var viewModel = {form: {text: 'bar', tags: []}};

      updateDomainModel(domainModel, viewModel, fakePermissions(),
                        fakeGroups());

      assert.equal(domainModel.text, viewModel.form.text);
    });

    it('doesn\'t touch other properties in domainModel', function() {
      var domainModel = {foo: 'foo', bar: 'bar'};
      var viewModel = {form: {foo: 'FOO', tags: []}};

      updateDomainModel(domainModel, viewModel, fakePermissions(),
                        fakeGroups());

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

      updateDomainModel(domainModel, viewModel, fakePermissions(),
                        fakeGroups());

      assert.deepEqual(
        domainModel.tags, ['foo', 'bar'],
        'The array of {tag: "text"} objects in  viewModel becomes an array ' +
        'of "text" strings in domainModel');
    });

    it('sets domainModel.permissions to private if vm.isPrivate', function() {
      var domainModel = {};
      var viewModel = {
        isPrivate: true,
        form: {
          text: 'foo',
        },
      };
      var permissions = fakePermissions();
      permissions.private = sinon.stub().returns('private permissions');

      updateDomainModel(domainModel, viewModel, permissions, fakeGroups());

      assert.equal(domainModel.permissions, 'private permissions');
    });

    it('sets domainModel.permissions to shared if !vm.isPrivate', function() {
      var domainModel = {};
      var viewModel = {
        isPrivate: false,
        form: {
          text: 'foo',
        },
      };
      var permissions = fakePermissions();
      permissions.shared = sinon.stub().returns('shared permissions');

      updateDomainModel(domainModel, viewModel, permissions, fakeGroups());

      assert.equal(domainModel.permissions, 'shared permissions');
    });
  });

  describe('link', function () {
    var link = require('../annotation').link;

    /** Return Angular's $rootScope. */
    function getRootScope() {
      var $rootScope;
      inject(function(_$rootScope_) {
        $rootScope = _$rootScope_;
      });
      return $rootScope;
    }

    var scope;
    var mockElement;
    var mockAttributes;
    var mockAnnotationController;
    var mockThreadController;
    var mockThreadFilterController;
    var mockDeepCountController;
    var mockControllers;

    beforeEach(function () {
      scope = getRootScope().$new();
      mockElement = {on: sinon.stub()};
      mockAttributes = undefined;  // Left undefined because link() doesn't use
                                   // it.
      mockAnnotationController = {
        editing: sinon.stub().returns(false),
        onKeydown: "annotationController.onKeydown"  // Sentinel value.
      };
      mockThreadController = {
        collapsed: true,
        toggleCollapsed: sinon.stub()
      };
      mockThreadFilterController = {
        active: sinon.stub(),
        freeze: sinon.stub()
      };
      mockDeepCountController = {
        count: sinon.stub()
      };
      mockControllers = [
        mockAnnotationController, mockThreadController,
        mockThreadFilterController, mockDeepCountController];
    });

    it('binds AnnotationController.onKeydown to "keydown"', function () {
      link(scope, mockElement, mockAttributes, mockControllers);

      assert.equal(1, mockElement.on.callCount);
      assert.equal(
        true,
        mockElement.on.calledWithExactly(
          'keydown', mockAnnotationController.onKeydown)
      );
    });

    it('increments the "edit" count when editing() becomes true', function () {
      link(scope, mockElement, mockAttributes, mockControllers);

      mockAnnotationController.editing.returns(true);
      scope.$digest();

      assert.equal(true, mockDeepCountController.count.calledOnce);
      assert.equal(
        true, mockDeepCountController.count.calledWithExactly('edit', 1)
      );
    });

    it('decrements the "edit" count when editing() turns false', function () {
      mockAnnotationController.editing.returns(true);
      link(scope, mockElement, mockAttributes, mockControllers);
      scope.$digest();

      mockAnnotationController.editing.returns(false);
      scope.$digest();

      assert.equal(
        true,
        mockDeepCountController.count.lastCall.calledWithExactly('edit', -1)
      );
    });

    it('decrements the edit count when destroyed while editing', function () {
      mockAnnotationController.editing.returns(true);
      link(scope, mockElement, mockAttributes, mockControllers);

      scope.$destroy();

      assert.equal(1, mockDeepCountController.count.callCount);
      assert.equal(
        true, mockDeepCountController.count.calledWithExactly('edit', -1)
      );
    });

    it('does not decrement the edit count when destroyed while not editing',
      function () {
        mockAnnotationController.editing.returns(false);
        link(scope, mockElement, mockAttributes, mockControllers);

        scope.$destroy();

        assert.equal(0, mockDeepCountController.count.callCount);
      }
    );

    it('deactivates the thread filter when editing() turns true', function () {
      mockAnnotationController.editing.returns(false);
      link(scope, mockElement, mockAttributes, mockControllers);

      mockAnnotationController.editing.returns(true);
      scope.$digest();

      assert.equal(1, mockThreadFilterController.active.callCount);
      assert.equal(
        true, mockThreadFilterController.active.calledWithExactly(false));
    });

    it('freezes the thread filter when editing', function () {
      mockAnnotationController.editing.returns(false);
      link(scope, mockElement, mockAttributes, mockControllers);

      mockAnnotationController.editing.returns(true);
      scope.$digest();

      assert.equal(1, mockThreadFilterController.freeze.callCount);
      assert.equal(
        true, mockThreadFilterController.freeze.calledWithExactly(true));
    });

    it('unfreezes the thread filter when editing becomes false', function () {
      mockAnnotationController.editing.returns(true);
      link(scope, mockElement, mockAttributes, mockControllers);
      scope.$digest();

      mockAnnotationController.editing.returns(false);
      scope.$digest();

      assert.equal(
        true,
        mockThreadFilterController.freeze.lastCall.calledWithExactly(false));
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
    var fakePermissions;
    var fakeSession;
    var fakeSettings;
    var fakeTags;
    var fakeTime;
    var fakeUrlEncodeFilter;
    var sandbox;

    function createDirective(annotation) {
      annotation = annotation || defaultAnnotation();
      var element = util.createDirective(document, 'annotation', {
        annotation: annotation,
      });
      return {
        annotation: annotation,
        controller: element.ctrl,
        element: element,
        scope: element.scope,
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
        user: 'acct:bill@localhost',
        updated: '2015-05-10T20:18:56.613388+00:00',
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
        .directive('annotation', annotationDirective());
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

      fakeSession = {
        state: {
          userid: 'acct:bill@localhost'
        }
      };

      fakeSettings = {
        serviceUrl: 'https://test.hypothes.is/',
      };

      fakeTags = {
        filter: sandbox.stub().returns('a while ago'),
        store: sandbox.stub()
      };

      fakeTime = {
        toFuzzyString: sandbox.stub().returns('a while ago'),
        decayingInterval: function () {},
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
      $provide.value('permissions', fakePermissions);
      $provide.value('session', fakeSession);
      $provide.value('settings', fakeSettings);
      $provide.value('tags', fakeTags);
      $provide.value('time', fakeTime);
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

    describe('initialization', function() {
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

      it('sets the permissions of new annotations', function() {
        // You can create annotations while logged out and then login.
        // When you login a new AnnotationController instance is created for
        // each of your annotations, and on initialization it will set the
        // annotation's permissions using your username from the session.
        var annotation = newAnnotation();
        annotation.user = annotation.permissions = undefined;
        annotation.group = '__world__';
        fakeSession.state.userid = 'acct:bill@localhost';
        fakePermissions.default = function (group) {
          return 'default permissions for ' + group;
        };

        createDirective(annotation);

        assert.equal(annotation.permissions,
          'default permissions for __world__');
      });

      it('preserves the permissions of existing annotations', function() {
        var annotation = newAnnotation();
        annotation.permissions = {
          permissions: {
            read: ['foo'],
            update: ['bar'],
            'delete': ['gar'],
            admin: ['har']
          }
        };
        var originalPermissions = JSON.parse(JSON.stringify(
          annotation.permissions));
        fakePermissions['default'] = function () {
          return 'new permissions';
        };
        fakePermissions.isShared = function () {};
        fakePermissions.isPrivate = function () {};
        createDirective(annotation);
        assert.deepEqual(annotation.permissions, originalPermissions);
      });

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

    describe('.editing()', function() {
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

    describe('.isHighlight()', function() {
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
        var annotation = defaultAnnotation();
        annotation.group = 'my group';
        annotation.permissions = {
          read: ['my-group'],
        };
        var controller = createDirective(annotation).controller;
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
          controller.isPrivate = true;
          var reply = {};
          fakeAnnotationMapper.createAnnotation.returns(reply);
          controller.reply();
          assert.deepEqual(reply.permissions, {
            read: ['justme']
          });
        }
      );

      it('sets the reply\'s group to be the same as its parent\'s', function() {
        var annotation = defaultAnnotation();
        annotation.group = 'my group';
        var controller = createDirective(annotation).controller;
        var reply = {};
        fakeAnnotationMapper.createAnnotation.returns(reply);
        controller.reply();
        assert.equal(reply.group, annotation.group);
      });
    });

    describe('#setPrivacy', function() {
      it('makes the annotation private when level is "private"', function() {
        var parts = createDirective();

        // Make this annotation shared.
        parts.controller.isPrivate = false;
        fakePermissions.isPrivate.returns(false);

        parts.annotation.$update = sinon.stub().returns(Promise.resolve());

        // Edit the annotation and make it private.
        parts.controller.edit();
        parts.controller.setPrivacy('private');
        fakePermissions.isPrivate.returns(true);

        return parts.controller.save().then(function() {
          // Verify that the permissions are updated once the annotation
          // is saved.
          assert.equal(parts.controller.isPrivate, true);
        });
      });

      it('makes the annotation shared when level is "shared"', function() {
        var parts = createDirective();
        parts.controller.isPrivate = true;
        parts.annotation.$update = sinon.stub().returns(Promise.resolve());
        parts.controller.edit();
        parts.controller.form.text = 'test';
        parts.controller.setPrivacy('shared');
        return parts.controller.save().then(function() {
          assert.equal(parts.controller.isPrivate, false);
        });
      });

      it('saves the "shared" visibility level to localStorage', function() {
        var parts = createDirective();
        parts.annotation.$update = sinon.stub().returns(Promise.resolve());
        parts.controller.edit();
        parts.controller.setPrivacy('shared');
        parts.controller.form.text = 'test';
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

    describe('relativeTimestamp', function() {
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
        assert.equal(controller.relativeTimestamp, null);
      });

      it('is updated when a new annotation is saved', function () {
        fakeTime.decayingInterval = function (date, callback) {
          callback();
        };

        // fake clocks are not required for this test
        clock.restore();

        annotation.updated = null;
        annotation.$create = function () {
          annotation.updated = (new Date).toString();
          return Promise.resolve(annotation);
        };
        var controller = createDirective(annotation).controller;
        controller.action = 'create';
        controller.form.text = 'test';
        return controller.save().then(function () {
          assert.equal(controller.relativeTimestamp, 'a while ago');
        });
      });

      it('is updated when a change to an existing annotation is saved',
       function () {
        fakeTime.toFuzzyString = function(date) {
          var ONE_MINUTE = 60 * 1000;
          if (Date.now() - new Date(date) < ONE_MINUTE) {
            return 'just now';
          } else {
            return 'ages ago';
          }
        };

        clock.tick(10 * 60 * 1000);

        annotation.$update = function () {
          this.updated = (new Date).toString();
          return Promise.resolve(this);
        }
        var controller = createDirective(annotation).controller;
        assert.equal(controller.relativeTimestamp, 'ages ago');
        controller.edit();
        controller.form.text = 'test';
        clock.restore();
        return controller.save().then(function () {
          assert.equal(controller.relativeTimestamp, 'just now');
        });
      });

      it('is updated on first digest', function() {
        var controller = createDirective(annotation).controller;
        $scope.$digest();
        assert.equal(controller.relativeTimestamp, 'a while ago');
      });

      it('is updated after a timeout', function() {
        fakeTime.decayingInterval = function (date, callback) {
          setTimeout(callback, 10);
        };
        var controller = createDirective(annotation).controller;
        fakeTime.toFuzzyString.returns('ages ago');
        $scope.$digest();
        clock.tick(11000);
        assert.equal(controller.relativeTimestamp, 'ages ago');
      });

      it('is no longer updated after the scope is destroyed', function() {
        var controller = createDirective(annotation).controller;
        $scope.$digest();
        $scope.$destroy();
        $timeout.flush();
        $timeout.verifyNoPendingTasks();
      });
    });

    describe('absoluteTimestamp', function () {
      it('returns the current time', function () {
        var annotation = defaultAnnotation();
        var controller = createDirective(annotation).controller;
        var expectedDate = new Date(annotation.updated);
        // the exact format of the result will depend on the current locale,
        // but check that at least the current year and time are present
        assert.match(controller.absoluteTimestamp, new RegExp('.*2015.*' +
          expectedDate.toLocaleTimeString()));
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
        controller.form.text = 'new annotation';
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

      it('shows a saving indicator when saving an annotation', function() {
        var controller = controllerWithActionCreate();
        var create;
        annotation.$create.returns(new Promise(function (resolve) {
          create = resolve;
        }));
        var saved = controller.save();
        assert.equal(controller.isSaving, true);
        assert.equal(controller.action, 'view');
        create();
        return saved.then(function () {
          assert.equal(controller.isSaving, false);
        });
      });

      it('reverts to edit mode if saving fails', function () {
        var controller = controllerWithActionCreate();
        var failCreation;
        annotation.$create.returns(new Promise(function (resolve, reject) {
          failCreation = reject;
        }));
        var saved = controller.save();
        assert.equal(controller.isSaving, true);
        failCreation({status: -1});
        return saved.then(function () {
          assert.equal(controller.isSaving, false);
          assert.ok(controller.editing());
        });
      });

      it(
        'Passes group:<id> to the server when saving a new annotation',
        function() {
          fakeGroups.focused = function () {
            return { id: 'test-id' }
          };
          var annotation = {
            user: 'acct:fred@hypothes.is',
            text: 'foo',
          };
          annotation.$create = sinon.stub().returns(Promise.resolve());
          var controller = createDirective(annotation).controller;
          controller.action = 'create';
          return controller.save().then(function() {
            assert.equal(annotation.$create.lastCall.thisValue.group,
              'test-id');
          });
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
        controller.form.text = 'updated text';
        return controller;
      }

      it(
        'flashes a generic error if the server cannot be reached',
        function() {
          var controller = controllerWithActionEdit();
          annotation.$update.returns(Promise.reject({
            status: -1
          }));
          return controller.save().then(function() {
            assert(fakeFlash.error.calledWith(
              'Service unreachable.', 'Saving annotation failed'));
          });
        }
      );

      it(
        'flashes an error if saving the annotation fails on the server',
        function() {
          var controller = controllerWithActionEdit();
          annotation.$update.returns(Promise.reject({
            status: 500,
            statusText: 'Server Error',
            data: {}
          }));
          return controller.save().then(function() {
            assert(fakeFlash.error.calledWith(
              '500 Server Error', 'Saving annotation failed'));
          });
        }
      );

      it(
        'doesn\'t flash an error if saving the annotation succeeds',
        function() {
          var controller = controllerWithActionEdit();
          annotation.$update.returns(Promise.resolve());
          controller.form.text = 'updated text';
          controller.save();
          assert(fakeFlash.error.notCalled);
        }
      );
    });

    describe('drafts', function() {
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
          tags: [{text: 'unsaved-tag'}],
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
        controller.form.text = 'test annotation';
        return controller.save().then(function() {
          assert.calledWith(fakeDrafts.remove, annotation);
        });
      });
    });

    describe('onAnnotationUpdated()', function() {
      it('updates vm.form.text', function() {
        var parts = createDirective();
        var updatedModel = {
          id: parts.annotation.id,
          text: 'new text',
        };

        $rootScope.$emit('annotationUpdated', updatedModel);

        assert.equal(parts.controller.form.text, 'new text');
      });

      it('doesn\'t update if a different annotation was updated', function() {
        var parts = createDirective();
        parts.controller.form.text = 'original text';
        var updatedModel = {
          id: 'different annotation id',
          text: 'new text',
        };

        $rootScope.$emit('annotationUpdated', updatedModel);

        assert.equal(parts.controller.form.text, 'original text');
      });
    });

    describe('onGroupFocused()', function() {
      it('if the annotation is being edited it updates drafts', function() {
        var parts = createDirective();
        parts.controller.isPrivate = true;
        parts.controller.edit();
        parts.controller.form.text = 'unsaved-text';
        parts.controller.form.tags = [];
        fakeDrafts.get = sinon.stub().returns({
          text: 'old-draft'
        });
        fakeDrafts.update = sinon.stub();

        $rootScope.$broadcast(events.GROUP_FOCUSED);

        assert.calledWith(
          fakeDrafts.update,
          parts.annotation, {isPrivate:true, tags:[], text:'unsaved-text'});
      });

      it('if the annotation isn\'t being edited it doesn\'t update drafts',
         function() {
           var parts = createDirective();
           parts.controller.isPrivate = true;
           fakeDrafts.update = sinon.stub();

           $rootScope.$broadcast(events.GROUP_FOCUSED);

           assert.notCalled(fakeDrafts.update);
         }
      );

      it('updates domainModel.group if the annotation is new', function () {
        var annotation = newAnnotation();
        annotation.group = 'old-group-id';
        createDirective(annotation);
        fakeGroups.focused = sandbox.stub().returns({id: 'new-group-id'});

        $rootScope.$broadcast(events.GROUP_FOCUSED);

        assert.equal(annotation.group, 'new-group-id');
      });

      it('does not update domainModel.group if the annotation is not new',
        function () {
          var annotation = oldAnnotation();
          annotation.group = 'old-group-id';
          createDirective(annotation);
          fakeGroups.focused = sandbox.stub().returns({id: 'new-group-id'});

          $rootScope.$broadcast(events.GROUP_FOCUSED);

          assert.equal(annotation.group, 'old-group-id');
        }
      );
    });


    describe('reverting edits', function () {
      // Simulate what happens when the user edits an annotation,
      // clicks Save, gets an error because the server fails to save the
      // annotation, then clicks Cancel - in the frontend the annotation should
      // be restored to its original value, the edits lost.
      it('restores the original text', function() {
        var controller = createDirective({
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

      // Test that editing reverting changes to an annotation with
      // no text resets the text to be empty.
      it('clears the text if the text was originally empty', function() {
        var controller = createDirective({
          id: 'test-annotation-id',
          user: 'acct:bill@localhost',
        }).controller;
        controller.edit();
        assert.equal(controller.action, 'edit');
        controller.form.text = 'this should be reverted';
        controller.revert();
        assert.equal(controller.form.text, void 0);
      });

      it('reverts to the most recently saved version',
        function () {

        var controller = createDirective({
          user: 'acct:bill@localhost',
          $create: function () {
            this.id = 'new-annotation-id';
            return Promise.resolve();
          },
          $update: function () {
            return Promise.resolve(this);
          },
        }).controller;
        controller.edit();
        controller.form.text = 'New annotation text';
        return controller.save().then(function () {
          controller.edit();
          controller.form.text = 'Updated annotation text';
          return controller.save();
        }).then(function () {
          controller.edit();
          controller.revert();
          assert.equal(controller.form.text, 'Updated annotation text');
        });
      });
    });
  });
});
