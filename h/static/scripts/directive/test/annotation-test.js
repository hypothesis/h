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

    var scope;
    var mockElement;
    var mockAttributes;
    var mockAnnotationController;
    var mockThreadController;
    var mockThreadFilterController;
    var mockDeepCountController;
    var mockControllers;

    beforeEach(function () {
      scope = util.ngModule(inject, '$rootScope').$new();
      mockElement = {on: sinon.stub()};
      mockAttributes = undefined;  // Left undefined because link() doesn't use
                                   // it.
      mockAnnotationController = {
        editing: sinon.stub().returns(false),
        onKeydown: "annotationController.onKeydown"  // Sentinel value.
      };
      mockThreadController = {
        collapsed: true,
        toggleCollapsed: sinon.stub(),
        parent: {
          toggleCollapsed: sinon.stub()
        }
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
    var fakeTime;
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

      var fakeTags = {
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

      it('edits new annotations on initialization', function() {
        var annotation = fixtures.newAnnotation();

        var controller = createDirective(annotation).controller;

        assert.isTrue(controller.editing());
      });

      it('edits annotations with drafts on initialization', function() {
        var annotation = fixtures.oldAnnotation();
        // The drafts service has some draft changes for this annotation.
        fakeDrafts.get.returns('foo');

        var controller = createDirective(annotation).controller;

        assert.isTrue(controller.editing());
      });

      it('does not edit new highlights on initialization', function() {
        var annotation = fixtures.newHighlight();
        // We have to set annotation.$create() because it'll try to call it.
        annotation.$create = sandbox.stub().returns({
          then: function() {}
        });

        var controller = createDirective(annotation).controller;

        assert.isFalse(controller.editing());
      });

      it('edits highlights with drafts on initialization', function() {
        var annotation = fixtures.oldHighlight();
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

    describe('relativeTimestamp', function() {
      var annotation;
      var clock;

      beforeEach(function() {
        clock = sinon.useFakeTimers();
        annotation = fixtures.defaultAnnotation();
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
          annotation.updated = (new Date()).toString();
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
          this.updated = (new Date()).toString();
          return Promise.resolve(this);
        };
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
        createDirective(annotation);
        $scope.$digest();
        $scope.$destroy();
        $timeout.verifyNoPendingTasks();
      });
    });

    describe('absoluteTimestamp', function () {
      it('returns the current time', function () {
        var annotation = fixtures.defaultAnnotation();
        var controller = createDirective(annotation).controller;
        var expectedDate = new Date(annotation.updated);
        // the exact format of the result will depend on the current locale,
        // but check that at least the current year and time are present
        assert.match(controller.absoluteTimestamp, new RegExp('.*2015.*' +
          expectedDate.toLocaleTimeString()));
      });
    });

    describe('deleteAnnotation() method', function() {
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
        annotation = fixtures.defaultAnnotation();
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
            assert($rootScope.$emit.calledWith(events.ANNOTATION_CREATED));
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
            return { id: 'test-id' };
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
        annotation = fixtures.defaultAnnotation();
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
        var annotation = fixtures.defaultAnnotation();
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

        $rootScope.$emit(events.ANNOTATION_UPDATED, updatedModel);

        assert.equal(parts.controller.form.text, 'new text');
      });

      it('doesn\'t update if a different annotation was updated', function() {
        var parts = createDirective();
        parts.controller.form.text = 'original text';
        var updatedModel = {
          id: 'different annotation id',
          text: 'new text',
        };

        $rootScope.$emit(events.ANNOTATION_UPDATED, updatedModel);

        assert.equal(parts.controller.form.text, 'original text');
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
        var parts = createDirective(fixtures.defaultAnnotation());
        parts.controller.form.text = '';
        parts.controller.form.tags = [];
        $rootScope.$emit(events.BEFORE_ANNOTATION_CREATED,
          fixtures.newAnnotation());
        assert.notCalled(fakeDrafts.remove);
      });

      it('does not remove the current annotation if it has text', function () {
        var annotation = fixtures.newAnnotation();
        var parts = createDirective(annotation);
        parts.controller.form.text = 'An incomplete thought';
        $rootScope.$emit(events.BEFORE_ANNOTATION_CREATED,
          fixtures.newAnnotation());
        assert.notCalled(fakeDrafts.remove);
      });

      it('does not remove the current annotation if it has tags', function () {
        var annotation = fixtures.newAnnotation();
        var parts = createDirective(annotation);
        parts.controller.form.tags = [{text: 'a-tag'}];
        $rootScope.$emit(events.BEFORE_ANNOTATION_CREATED,
          fixtures.newAnnotation());
        assert.notCalled(fakeDrafts.remove);
      });
    });

    describe('when component is destroyed', function () {
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

        parts.scope.$broadcast('$destroy');

        assert.calledWith(
          fakeDrafts.update,
          parts.annotation, {isPrivate:true, tags:[], text:'unsaved-text'});
      });

      it('if the annotation isn\'t being edited it doesn\'t update drafts', function() {
         var parts = createDirective();
         parts.controller.isPrivate = true;
         fakeDrafts.update = sinon.stub();

         parts.scope.$broadcast('$destroy');

         assert.notCalled(fakeDrafts.update);
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

    describe('annotation metadata', function () {
      function findLink(directive) {
        var links = directive.element[0]
          .querySelectorAll('header .annotation-header__timestamp');
        return links[links.length-1];
      }

      it('displays HTML links when in-context links are not available', function () {
        var annotation = Object.assign({}, fixtures.defaultAnnotation(), {
          links: {html: 'https://test.hypothes.is/a/deadbeef'},
        });
        var directive = createDirective(annotation);
        assert.equal(findLink(directive).href, annotation.links.html);
      });

      it('displays in-context links when available', function () {
        var annotation = Object.assign({}, fixtures.defaultAnnotation(), {
          links: {
            html: 'https://test.hypothes.is/a/deadbeef',
            incontext: 'https://hpt.is/deadbeef'
          },
        });
        var directive = createDirective(annotation);
        assert.equal(findLink(directive).href, annotation.links.incontext);
      });
    });
  });
});
