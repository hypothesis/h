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
  var fakeLocation = null;
  var fakeParams = null;
  var fakeSession = null;
  var fakeSettings = null;
  var fakeGroups = null;
  var fakeRoute = null;
  var fakeSettings = null;
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
      logout: sandbox.stub().returns(Promise.resolve()),
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

    fakeLocation = {
      search: sandbox.stub().returns({})
    };

    fakeParams = {id: 'test'};

    fakeSession = {
      load: sandbox.stub().returns(Promise.resolve({userid: null})),
    };

    fakeGroups = {focus: sandbox.spy()};

    fakeRoute = {reload: sandbox.spy()};

    fakeWindow = {
      top: {},
      confirm: sandbox.stub()
    };

    fakeSettings = {
      firstRun: false,
    };

    $provide.value('annotationUI', fakeAnnotationUI);
    $provide.value('auth', fakeAuth);
    $provide.value('drafts', fakeDrafts);
    $provide.value('features', fakeFeatures);
    $provide.value('session', fakeSession);
    $provide.value('settings', fakeSettings);
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

  it('auth.status is "unknown" on startup', function () {
    createController();
    assert.equal($scope.auth.status, 'unknown');
  });

  it('sets auth.status to "signed-out" if userid is null', function () {
    createController();
    return fakeSession.load().then(function () {
      assert.equal($scope.auth.status, 'signed-out');
    });
  });

  it('sets auth.status to "signed-in" if userid is non-null', function () {
    fakeSession.load = function () {
      return Promise.resolve({userid: 'acct:jim@hypothes.is'});
    };
    createController();
    return fakeSession.load().then(function () {
      assert.equal($scope.auth.status, 'signed-in');
    });
  });

  it('sets userid, username, and provider properties at login', function () {
    fakeSession.load = function () {
      return Promise.resolve({userid: 'acct:jim@hypothes.is'});
    };
    createController();
    return fakeSession.load().then(function () {
      assert.equal($scope.auth.userid, 'acct:jim@hypothes.is');
      assert.equal($scope.auth.username, 'jim');
      assert.equal($scope.auth.provider, 'hypothes.is');
    });
  });

  it('updates auth when the logged-in user changes', function () {
    createController();
    return fakeSession.load().then(function () {
      $scope.$broadcast(events.USER_CHANGED, {
        initialLoad: false,
        userid: 'acct:john@hypothes.is',
      });
      assert.deepEqual($scope.auth, {
        status: 'signed-in',
        userid: 'acct:john@hypothes.is',
        username: 'john',
        provider: 'hypothes.is',
      });
    });
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
