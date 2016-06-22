/* jshint node: true */
'use strict';

var angular = require('angular');
var proxyquire = require('proxyquire');

var events = require('../../events');
var fixtures = require('../../test/annotation-fixtures');
var testUtil = require('../../test/util');
var util = require('./util');

var inject = angular.mock.inject;

/**
 * Returns the annotation directive with helpers stubbed out.
 */
function annotationDirective() {
  var noop = function () { return ''; };

  var annotation = proxyquire('../annotation', {
    angular: testUtil.noCallThru(angular),
    '../filter/document-domain': noop,
    '../filter/document-title': noop,
    '../filter/persona': {
      username: noop,
    }
  });

  return annotation.directive;
}

describe('annotation', function() {
  describe('updateDomainModel()', function() {
    var updateDomainModel = require('../annotation').updateDomainModel;

    function fakePermissions() {
      return {
        shared: function() {},
        private: function() {},
      };
    }

    it('copies text from viewModel into domainModel', function() {
      var domainModel = {};
      var viewModel = {state: sinon.stub.returns({text: 'bar', tags: []})};

      updateDomainModel(domainModel, viewModel, fakePermissions());

      assert.equal(domainModel.text, viewModel.state().text);
    });

    it('overwrites text in domainModel', function() {
      var domainModel = {text: 'foo'};
      var viewModel = {state: sinon.stub.returns({text: 'bar', tags: []})};

      updateDomainModel(domainModel, viewModel, fakePermissions());

      assert.equal(domainModel.text, viewModel.state().text);
    });

    it('doesn\'t touch other properties in domainModel', function() {
      var domainModel = {foo: 'foo', bar: 'bar'};
      var viewModel = {state: sinon.stub.returns({foo: 'FOO', tags: []})};

      updateDomainModel(domainModel, viewModel, fakePermissions());

      assert.equal(
        domainModel.bar, 'bar',
        'updateDomainModel() should not touch properties of domainModel' +
        'that don\'t exist in viewModel');
    });

    it('copies tag texts from viewModel into domainModel', function() {
      var domainModel = {};
      var viewModel = {
        state: sinon.stub().returns({
          tags: ['foo', 'bar'],
        })
      };

      updateDomainModel(domainModel, viewModel, fakePermissions());

      assert.deepEqual(domainModel.tags, ['foo', 'bar']);
    });

    it('sets domainModel.permissions to private if vm.isPrivate', function() {
      var domainModel = {};
      var viewModel = {
        state: sinon.stub().returns({
          isPrivate: true,
          text: 'foo',
        }),
      };
      var permissions = fakePermissions();
      permissions.private = sinon.stub().returns('private permissions');

      updateDomainModel(domainModel, viewModel, permissions);

      assert.equal(domainModel.permissions, 'private permissions');
    });

    it('sets domainModel.permissions to shared if !vm.isPrivate', function() {
      var domainModel = {};
      var viewModel = {
        state: sinon.stub().returns({
          isPrivate: false,
          text: 'foo',
        }),
      };
      var permissions = fakePermissions();
      permissions.shared = sinon.stub().returns('shared permissions');

      updateDomainModel(domainModel, viewModel, permissions);

      assert.equal(domainModel.permissions, 'shared permissions');
    });
  });

  describe('AnnotationController', function() {
    var $q;
    var $rootScope;
    var $scope;
    var $timeout;
    var $window;
    var fakeAnnotationMapper;
    var fakeDrafts;
    var fakeFlash;
    var fakeGroups;
    var fakePermissions;
    var fakeSession;
    var sandbox;

    function createDirective(annotation) {
      annotation = annotation || fixtures.defaultAnnotation();
      var element = util.createDirective(document, 'annotation', {
        annotation: annotation,
      });

      // A new annotation won't have any saved drafts yet.
      if (!annotation.id) {
        fakeDrafts.get.returns(null);
      }

      return {
        annotation: annotation,
        controller: element.ctrl,
        element: element,
        scope: element.scope,
      };
    }



    before(function() {
      angular.module('h', [])
        .directive('annotation', annotationDirective());
    });

    beforeEach(angular.mock.module('h'));
    beforeEach(angular.mock.module(function($provide) {
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

      var fakeAnnotationUI = {};

      fakeDrafts = {
        update: sandbox.stub(),
        remove: sandbox.stub(),
        get: sandbox.stub()
      };

      var fakeFeatures = {
        flagEnabled: sandbox.stub().returns(true),
      };

      fakeFlash = {
        error: sandbox.stub(),
      };

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

      var fakeSettings = {
        serviceUrl: 'https://test.hypothes.is/',
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
        var annotation = fixtures.newAnnotation();
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
        var annotation = fixtures.newAnnotation();
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

      it('sets the tags and text fields for new annotations', function () {
        var annotation = fixtures.newAnnotation();
        delete annotation.tags;
        delete annotation.text;
        createDirective(annotation);
        assert.equal(annotation.text, '');
        assert.deepEqual(annotation.tags, []);
      });

      it('preserves the permissions of existing annotations', function() {
        var annotation = fixtures.newAnnotation();
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
        var annotation = fixtures.newHighlight();
        // The user is logged-in.
        annotation.user = fakeSession.state.userid = 'acct:bill@localhost';
        annotation.$create = sandbox.stub().returns({
          then: function() {}
        });

        createDirective(annotation);

        assert.called(annotation.$create);
      });

      it('saves new highlights to drafts if not logged in', function() {
        var annotation = fixtures.newHighlight();
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
        var annotation = fixtures.newAnnotation();
        annotation.$create = sandbox.stub().returns({
          then: function() {}
        });

        createDirective(annotation);

        assert.notCalled(annotation.$create);
      });

      it('does not save old highlights on initialization', function() {
        var annotation = fixtures.oldHighlight();
        annotation.$create = sandbox.stub().returns({
          then: function() {}
        });

        createDirective(annotation);

        assert.notCalled(annotation.$create);
      });

      it('does not save old annotations on initialization', function() {
        var annotation = fixtures.oldAnnotation();
        annotation.$create = sandbox.stub().returns({
          then: function() {}
        });

        createDirective(annotation);

        assert.notCalled(annotation.$create);
      });

      it('creates drafts for new annotations on initialization', function() {
        var annotation = fixtures.newAnnotation();
        createDirective(annotation);
        assert.calledWith(fakeDrafts.update, annotation, {
          isPrivate: false,
          tags: annotation.tags,
          text: annotation.text,
        });
      });

      it('does not create drafts for new highlights on initialization', function() {
        var annotation = fixtures.newHighlight();
        // We have to set annotation.$create() because it'll try to call it.
        annotation.$create = sandbox.stub().returns({
          then: function() {}
        });
        assert.notCalled(fakeDrafts.update);
      });

      it('edits annotations with drafts on initialization', function() {
        var annotation = fixtures.oldAnnotation();
        // The drafts service has some draft changes for this annotation.
        fakeDrafts.get.returns({text: 'foo', tags: []});

        var controller = createDirective(annotation).controller;

        assert.isTrue(controller.editing());
      });
    });

    describe('#editing()', function() {
      it('returns false if the annotation does not have a draft', function () {
        var controller = createDirective().controller;
        assert.notOk(controller.editing());
      });

      it('returns true if the annotation has a draft', function () {
        var controller = createDirective().controller;
        fakeDrafts.get.returns({tags: [], text: '', isPrivate: false});
        assert.isTrue(controller.editing());
      });

      it('returns false if the annotation has a draft but is being saved', function () {
        var controller = createDirective().controller;
        fakeDrafts.get.returns({tags: [], text: '', isPrivate: false});
        controller.isSaving = true;
        assert.isFalse(controller.editing());
      });
    });

    describe('.isHighlight()', function() {
      it('returns true for new highlights', function() {
        var annotation = fixtures.newHighlight();
        // We need to define $create because it'll try to call it.
        annotation.$create = function() {return {then: function() {}};};

        var vm = createDirective(annotation).controller;

        assert.isTrue(vm.isHighlight());
      });

      it('returns false for new annotations', function() {
        var annotation = fixtures.newAnnotation();

        var vm = createDirective(annotation).controller;

        assert.isFalse(vm.isHighlight());
      });

      it('returns false for page notes', function() {
        var annotation = fixtures.oldPageNote();

        var vm = createDirective(annotation).controller;

        assert.isFalse(vm.isHighlight());
      });

      it('returns false for replies', function() {
        var annotation = fixtures.oldReply();

        var vm = createDirective(annotation).controller;

        assert.isFalse(vm.isHighlight());
      });

      it('returns false for annotations with text but no tags', function() {
        var annotation = fixtures.oldAnnotation();
        annotation.text = 'This is my annotation';
        annotation.tags = [];

        var vm = createDirective(annotation).controller;

        assert.isFalse(vm.isHighlight());
      });

      it('returns false for annotations with tags but no text', function() {
        var annotation = fixtures.oldAnnotation();
        annotation.text = '';
        annotation.tags = ['foo'];

        var vm = createDirective(annotation).controller;

        assert.isFalse(vm.isHighlight());
      });

      it('returns true for annotations with no text or tags', function() {
        var annotation = fixtures.oldAnnotation();
        annotation.text = '';
        annotation.tags = [];

        var vm = createDirective(annotation).controller;

        assert.isTrue(vm.isHighlight());
      });
    });

    describe('when the annotation is a highlight', function() {
      var annotation;

      beforeEach(function() {
        annotation = fixtures.defaultAnnotation();
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
        annotation = fixtures.defaultAnnotation();
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
        var annotation = fixtures.defaultAnnotation();
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
          fakePermissions.isPrivate.returns(true);
          var reply = {};
          fakeAnnotationMapper.createAnnotation.returns(reply);
          controller.reply();
          assert.deepEqual(reply.permissions, {
            read: ['justme']
          });
        }
      );

      it('sets the reply\'s group to be the same as its parent\'s', function() {
        var annotation = fixtures.defaultAnnotation();
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
        parts.controller.setPrivacy('private');
        assert.calledWith(fakeDrafts.update, parts.controller.annotation, sinon.match({
          isPrivate: true,
        }));
      });

      it('makes the annotation shared when level is "shared"', function() {
        var parts = createDirective();
        parts.controller.setPrivacy('shared');
        assert.calledWith(fakeDrafts.update, parts.controller.annotation, sinon.match({
          isPrivate: false,
        }));
      });

      it('sets the default visibility level', function() {
        var parts = createDirective();
        parts.controller.setPrivacy('shared');
        assert.calledWith(fakePermissions.setDefault, 'shared');
      });

      it('doesn\'t save the visibility if the annotation is a reply', function() {
        var parts = createDirective(fixtures.oldReply());
        parts.controller.setPrivacy('private');
        assert.notCalled(fakePermissions.setDefault);
      });
    });

    describe('#hasContent', function() {
      it('returns false if the annotation has no tags or text', function() {
        var controller = createDirective(fixtures.oldHighlight()).controller;
        assert.ok(!controller.hasContent());
      });

      it('returns true if the annotation has tags or text', function() {
        var controller = createDirective(fixtures.oldAnnotation()).controller;
        assert.ok(controller.hasContent());
      });
    });

    describe('#hasQuotes', function() {
      it('returns false if the annotation has no quotes', function() {
        var annotation = fixtures.defaultAnnotation();
        annotation.target = [{}];
        var controller = createDirective(annotation).controller;

        assert.isFalse(controller.hasQuotes());
      });

      it('returns true if the annotation has quotes', function() {
        var annotation = fixtures.defaultAnnotation();
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

    describe('#delete()', function() {
      beforeEach(function() {
        fakeAnnotationMapper.deleteAnnotation = sandbox.stub();
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
        function(done) {
          var parts = createDirective();
          sandbox.stub($window, 'confirm').returns(false);
          parts.controller['delete']().then(function() {
            assert.notCalled(fakeAnnotationMapper.deleteAnnotation);
            done();
          });
          $timeout.flush();
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
        annotation = fixtures.newAnnotation();
        annotation.$create = sandbox.stub();
      });

      function createController() {
        return createDirective(annotation).controller;
      }

      it('removes the draft when saving an annotation succeeds', function () {
        var controller = createController();
        annotation.$create.returns(Promise.resolve());
        return controller.save().then(function () {
          assert.calledWith(fakeDrafts.remove, annotation);
        });
      });

      it('emits annotationCreated when saving an annotation succeeds', function () {
        var controller = createController();
        sandbox.spy($rootScope, '$emit');
        annotation.$create.returns(Promise.resolve());
        return controller.save().then(function() {
          assert($rootScope.$emit.calledWith(events.ANNOTATION_CREATED));
        });
      });

      it('flashes a generic error if the server can\'t be reached', function () {
        var controller = createController();
        annotation.$create.returns(Promise.reject({
          status: 0
        }));
        return controller.save().then(function() {
          assert(fakeFlash.error.calledWith(
            'Service unreachable.', 'Saving annotation failed'));
        });
      });

      it('flashes an error if saving the annotation fails on the server', function () {
        var controller = createController();
        annotation.$create.returns(Promise.reject({
          status: 500,
          statusText: 'Server Error',
          data: {}
        }));
        return controller.save().then(function() {
          assert(fakeFlash.error.calledWith(
            '500 Server Error', 'Saving annotation failed'));
        });
      });

      it('doesn\'t flash an error when saving an annotation succeeds', function() {
        var controller = createController();
        annotation.$create.returns(Promise.resolve());
        controller.save();
        assert(fakeFlash.error.notCalled);
      });

      it('shows a saving indicator when saving an annotation', function() {
        var controller = createController();
        var create;
        annotation.$create.returns(new Promise(function (resolve) {
          create = resolve;
        }));
        var saved = controller.save();
        assert.equal(controller.isSaving, true);
        create();
        return saved.then(function () {
          assert.equal(controller.isSaving, false);
        });
      });

      it('does not remove the draft if saving fails', function () {
        var controller = createController();
        var failCreation;
        annotation.$create.returns(new Promise(function (resolve, reject) {
          failCreation = reject;
        }));
        var saved = controller.save();
        assert.equal(controller.isSaving, true);
        failCreation({status: -1});
        return saved.then(function () {
          assert.equal(controller.isSaving, false);
          assert.notCalled(fakeDrafts.remove);
        });
      });

      it(
        'Passes group:<id> to the server when saving a new annotation',
        function() {
          fakeGroups.focused = function () {
            return { id: 'test-id' };
          };
          var annotation = {
            user: 'acct:fred@hypothes.is',
            text: 'foo',
          };
          annotation.$create = sinon.stub().returns(Promise.resolve());
          var controller = createDirective(annotation).controller;
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
        annotation = fixtures.defaultAnnotation();
        annotation.$update = sandbox.stub();
        fakeDrafts.get.returns({text: 'unsaved change'});
      });

      function createController() {
        return createDirective(annotation).controller;
      }

      it(
        'flashes a generic error if the server cannot be reached',
        function() {
          var controller = createController();
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
          var controller = createController();
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
          var controller = createController();
          annotation.$update.returns(Promise.resolve());
          controller.save();
          assert(fakeFlash.error.notCalled);
        }
      );
    });

    describe('drafts', function() {
      it('starts editing immediately if there is a draft', function() {
        fakeDrafts.get.returns({
          tags: ['unsaved'],
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
        assert.deepEqual(controller.state().tags, ['unsaved-tag']);
        assert.equal(controller.state().text, 'unsaved-text');
      });

      it('removes the draft when changes are discarded', function() {
        var parts = createDirective();
        parts.controller.edit();
        parts.controller.revert();
        assert.calledWith(fakeDrafts.remove, parts.annotation);
      });

      it('removes the draft when changes are saved', function() {
        var annotation = fixtures.defaultAnnotation();
        annotation.$update = sandbox.stub().returns(Promise.resolve());
        var controller = createDirective(annotation).controller;
        fakeDrafts.get.returns({text: 'unsaved changes'});
        return controller.save().then(function() {
          assert.calledWith(fakeDrafts.remove, annotation);
        });
      });
    });

    describe('onAnnotationUpdated()', function() {
      it('updates vm.annotation', function() {
        var parts = createDirective();
        var updatedModel = {
          id: parts.annotation.id,
          links: {html: 'http://hyp.is/new-link'}
        };
        parts.controller.annotation = updatedModel;
        $rootScope.$emit(events.ANNOTATION_UPDATED, updatedModel);
        assert.equal(parts.controller.linkHTML, 'http://hyp.is/new-link');
      });

      it('doesn\'t update if a different annotation was updated', function() {
        var parts = createDirective();
        var updatedModel = {
          id: 'different annotation id',
          links: {html: 'http://hyp.is/new-link'},
        };

        $rootScope.$emit(events.ANNOTATION_UPDATED, updatedModel);
        assert.notEqual(parts.controller.linkHTML, 'http://hyp.is/new-link');
      });
    });

    describe('when another new annotation is created', function () {
      it('removes the current annotation if empty', function () {
        var annotation = fixtures.newEmptyAnnotation();
        createDirective(annotation);
        $rootScope.$emit(events.BEFORE_ANNOTATION_CREATED,
          fixtures.newAnnotation());
        assert.calledWith(fakeDrafts.remove, annotation);
      });

      it('does not remove the current annotation if is is not new', function () {
        createDirective(fixtures.defaultAnnotation());
        fakeDrafts.get.returns({text: '', tags: []});
        $rootScope.$emit(events.BEFORE_ANNOTATION_CREATED,
          fixtures.newAnnotation());
        assert.notCalled(fakeDrafts.remove);
      });

      it('does not remove the current annotation if it has text', function () {
        var annotation = fixtures.newAnnotation();
        createDirective(annotation);
        fakeDrafts.get.returns({text: 'An incomplete thought'});
        $rootScope.$emit(events.BEFORE_ANNOTATION_CREATED,
          fixtures.newAnnotation());
        assert.notCalled(fakeDrafts.remove);
      });

      it('does not remove the current annotation if it has tags', function () {
        var annotation = fixtures.newAnnotation();
        createDirective(annotation);
        fakeDrafts.get.returns({tags: ['a-tag']});
        $rootScope.$emit(events.BEFORE_ANNOTATION_CREATED,
          fixtures.newAnnotation());
        assert.notCalled(fakeDrafts.remove);
      });
    });

    describe('onGroupFocused()', function() {
      it('updates domainModel.group if the annotation is new', function () {
        var annotation = fixtures.newAnnotation();
        annotation.group = 'old-group-id';
        createDirective(annotation);
        fakeGroups.focused = sandbox.stub().returns({id: 'new-group-id'});

        $rootScope.$broadcast(events.GROUP_FOCUSED);

        assert.equal(annotation.group, 'new-group-id');
      });

      it('does not update domainModel.group if the annotation is not new',
        function () {
          var annotation = fixtures.oldAnnotation();
          annotation.group = 'old-group-id';
          createDirective(annotation);
          fakeGroups.focused = sandbox.stub().returns({id: 'new-group-id'});

          $rootScope.$broadcast(events.GROUP_FOCUSED);

          assert.equal(annotation.group, 'old-group-id');
        }
      );
    });


    describe('reverting edits', function () {
      it('removes the current draft', function() {
        var controller = createDirective(fixtures.defaultAnnotation()).controller;
        controller.edit();
        controller.revert();
        assert.calledWith(fakeDrafts.remove, controller.annotation);
      });
    });

    describe('tag display', function () {
      it('displays annotation tags', function () {
        var directive = createDirective({
          id: '1234',
          tags: ['atag']
        });
        var links = [].slice.apply(directive.element[0].querySelectorAll('a'));
        var tagLinks = links.filter(function (link) {
          return link.textContent === 'atag';
        });
        assert.equal(tagLinks.length, 1);
        assert.equal(tagLinks[0].href,
                     'https://test.hypothes.is/stream?q=tag:atag');
      });
    });

    describe('annotation links', function () {
      it('linkInContext uses the in-context links when available', function () {
        var annotation = Object.assign({}, fixtures.defaultAnnotation(), {
          links: {
            html: 'https://test.hypothes.is/a/deadbeef',
            incontext: 'https://hpt.is/deadbeef'
          },
        });
        var controller = createDirective(annotation).controller;

        assert.equal(controller.linkInContext, annotation.links.incontext);
      });

      it('linkInContext falls back to the HTML link when in-context links are missing', function () {
        var annotation = Object.assign({}, fixtures.defaultAnnotation(), {
          links: {
            html: 'https://test.hypothes.is/a/deadbeef',
          },
        });
        var controller = createDirective(annotation).controller;

        assert.equal(controller.linkInContext, annotation.links.html);
      });

      it('linkHTML uses the HTML link when available', function () {
        var annotation = Object.assign({}, fixtures.defaultAnnotation(), {
          links: {
            html: 'https://test.hypothes.is/a/deadbeef',
            incontext: 'https://hpt.is/deadbeef'
          },
        });
        var controller = createDirective(annotation).controller;

        assert.equal(controller.linkHTML, annotation.links.html);
      });

      it('linkInContext is blank when unknown', function () {
        var annotation = fixtures.defaultAnnotation();
        var controller = createDirective(annotation).controller;

        assert.equal(controller.linkInContext, '');
      });

      it('linkHTML is blank when unknown', function () {
        var annotation = fixtures.defaultAnnotation();
        var controller = createDirective(annotation).controller;

        assert.equal(controller.linkHTML, '');
      });
    });
  });
});
