'use strict';

var angular = require('angular');

var events = require('../events');

describe('AppController', function () {
  var $controller = null;
  var $scope = null;
  var $rootScope = null;
  var fakeAnnotationUI = null;
  var fakeAuth = null;
  var fakeDrafts = null;
  var fakeFeatures = null;
  var fakeIdentity = null;
  var fakeLocation = null;
  var fakeParams = null;
  var fakeSession = null;
  var fakeGroups = null;
  var fakeRoute = null;
  var fakeWindow = null;

  var sandbox = null;

  var createController = function (locals) {
    locals = locals || {};
    locals.$scope = $scope;
    return $controller('AppController', locals);
  };

  before(function () {
    return angular.module('h', [])
      .controller('AppController', require('../app-controller'))
      .controller('AnnotationUIController', angular.noop);
  });

  beforeEach(angular.mock.module('h'));

  beforeEach(angular.mock.module(function ($provide) {
    sandbox = sinon.sandbox.create();

    fakeAnnotationUI = {
      tool: 'comment',
      clearSelectedAnnotations: sandbox.spy()
    };

    fakeAuth = {
      userid: sandbox.stub()
    };

    fakeDrafts = {
      contains: sandbox.stub(),
      remove: sandbox.spy(),
      all: sandbox.stub().returns([]),
      discard: sandbox.spy(),
      count: sandbox.stub().returns(0),
      unsaved: sandbox.stub().returns([])
    };

    fakeFeatures = {
      fetch: sandbox.spy(),
      flagEnabled: sandbox.stub().returns(false)
    };

    fakeIdentity = {
      watch: sandbox.spy(),
      request: sandbox.spy(),
      logout: sandbox.stub()
    };

    fakeLocation = {
      search: sandbox.stub().returns({})
    };

    fakeParams = {id: 'test'};

    fakeSession = {};

    fakeGroups = {focus: sandbox.spy()};

    fakeRoute = {reload: sandbox.spy()};

    fakeWindow = {
      top: {},
      confirm: sandbox.stub()
    };

    $provide.value('annotationUI', fakeAnnotationUI);
    $provide.value('auth', fakeAuth);
    $provide.value('drafts', fakeDrafts);
    $provide.value('features', fakeFeatures);
    $provide.value('identity', fakeIdentity);
    $provide.value('session', fakeSession);
    $provide.value('groups', fakeGroups);
    $provide.value('$route', fakeRoute);
    $provide.value('$location', fakeLocation);
    $provide.value('$routeParams', fakeParams);
    $provide.value('$window', fakeWindow);
  }));

  beforeEach(angular.mock.inject(function (_$controller_, _$rootScope_) {
    $controller = _$controller_;
    $rootScope = _$rootScope_;
    $scope = $rootScope.$new();
  }));

  afterEach(function () {
    sandbox.restore();
  });

  describe('isSidebar property', function () {

    it('is false if the window is the top window', function () {
      fakeWindow.top = fakeWindow;
      createController();
      assert.isFalse($scope.isSidebar);
    });

    it('is true if the window is not the top window', function () {
      fakeWindow.top = {};
      createController();
      assert.isTrue($scope.isSidebar);
    });
  });

  it('watches the identity service for identity change events', function () {
    createController();
    assert.calledOnce(fakeIdentity.watch);
  });

  it('auth.status is "unknown" on startup', function () {
    createController();
    assert.equal($scope.auth.status, 'unknown');
  });

  it('sets auth.status to "signed-out" when the identity has been checked but the user is not authenticated', function () {
    createController();
    var identityCallbackArgs = fakeIdentity.watch.args[0][0];
    identityCallbackArgs.onready();
    assert.equal($scope.auth.status, 'signed-out');
  });

  it('sets auth.status to "signed-in" when the identity has been checked and the user is authenticated', function () {
    createController();
    fakeAuth.userid.withArgs('test-assertion').returns('acct:hey@joe');
    var identityCallbackArgs = fakeIdentity.watch.args[0][0];
    identityCallbackArgs.onlogin('test-assertion');
    assert.equal($scope.auth.status, 'signed-in');
  });

  it('sets userid, username, and provider properties at login', function () {
    createController();
    fakeAuth.userid.withArgs('test-assertion').returns('acct:hey@joe');
    var identityCallbackArgs = fakeIdentity.watch.args[0][0];
    identityCallbackArgs.onlogin('test-assertion');
    assert.equal($scope.auth.userid, 'acct:hey@joe');
    assert.equal($scope.auth.username, 'hey');
    assert.equal($scope.auth.provider, 'joe');
  });

  it('sets auth.status to "signed-out" at logout', function () {
    createController();
    var identityCallbackArgs = fakeIdentity.watch.args[0][0];
    identityCallbackArgs.onlogout();
    assert.equal($scope.auth.status, "signed-out");
  });

  it('does not show login form for logged in users', function () {
    createController();
    assert.isFalse($scope.accountDialog.visible);
  });

  it('does not show the share dialog at start', function () {
    createController();
    assert.isFalse($scope.shareDialog.visible);
  });

  it('does not reload the view when the logged-in user changes on first load', function () {
    createController();
    fakeRoute.reload = sinon.spy();
    $scope.$broadcast(events.USER_CHANGED, {initialLoad: true});
    assert.notCalled(fakeRoute.reload);
  });

  it('reloads the view when the logged-in user changes after first load', function () {
    createController();
    fakeRoute.reload = sinon.spy();
    $scope.$broadcast(events.USER_CHANGED, {initialLoad: false});
    assert.calledOnce(fakeRoute.reload);
  });

  describe('logout()', function () {
    it('prompts the user if there are drafts', function () {
      fakeDrafts.count.returns(1);
      createController();

      $scope.logout();

      assert.equal(fakeWindow.confirm.callCount, 1);
    });

    it('emits "annotationDeleted" for each unsaved draft annotation', function () {
      fakeDrafts.unsaved = sandbox.stub().returns(
        ["draftOne", "draftTwo", "draftThree"]
      );
      createController();
      $rootScope.$emit = sandbox.stub();

      $scope.logout();

      assert($rootScope.$emit.calledThrice);
      assert.deepEqual(
        $rootScope.$emit.firstCall.args, ["annotationDeleted", "draftOne"]);
      assert.deepEqual(
        $rootScope.$emit.secondCall.args, ["annotationDeleted", "draftTwo"]);
      assert.deepEqual(
        $rootScope.$emit.thirdCall.args, ["annotationDeleted", "draftThree"]);
    });

    it('discards draft annotations', function () {
      createController();

      $scope.logout();

      assert(fakeDrafts.discard.calledOnce);
    });

    it('does not emit "annotationDeleted" if the user cancels the prompt', function () {
      createController();
      fakeDrafts.count.returns(1);
      $rootScope.$emit = sandbox.stub();
      fakeWindow.confirm.returns(false);

      $scope.logout();

      assert($rootScope.$emit.notCalled);
    });

    it('does not discard drafts if the user cancels the prompt', function () {
      createController();
      fakeDrafts.count.returns(1);
      fakeWindow.confirm.returns(false);

      $scope.logout();

      assert(fakeDrafts.discard.notCalled);
    });

    it('does not prompt if there are no drafts', function () {
      createController();
      fakeDrafts.count.returns(0);

      $scope.logout();

      assert.equal(fakeWindow.confirm.callCount, 0);
    });
  });
});
