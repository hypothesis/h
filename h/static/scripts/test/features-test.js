'use strict';

var features = require('../features');

describe('h:features', function () {

  var fakeLog;
  var fakeSession;

  beforeEach(function () {
    fakeLog = {
      warn: sinon.stub(),
    };
    fakeSession = {
      load: sinon.stub(),
      state: {
        features: {
          'feature_on': true,
          'feature_off': false,
        },
      },
    };
  });

  describe('flagEnabled', function () {
    it('should retrieve features data', function () {
      var features_ = features(fakeLog, fakeSession);
      assert.equal(features_.flagEnabled('feature_on'), true);
      assert.equal(features_.flagEnabled('feature_off'), false);
    });

    it('should return false if features have not been loaded', function () {
      var features_ = features(fakeLog, fakeSession);
      // simulate feature data not having been loaded yet
      fakeSession.state = {};
      assert.equal(features_.flagEnabled('feature_on'), false);
    });

    it('should trigger a refresh of session data', function () {
      var features_ = features(fakeLog, fakeSession);
      features_.flagEnabled('feature_on');
      assert.calledOnce(fakeSession.load);
    });

    it('should return false for unknown flags', function () {
      var features_ = features(fakeLog, fakeSession);
      assert.isFalse(features_.flagEnabled('unknown_feature'));
    });
  });
});
