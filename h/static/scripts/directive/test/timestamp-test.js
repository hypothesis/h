'use strict';

var angular = require('angular');

var util = require('./util');

describe('timestamp', function () {
  var clock;
  var fakeTime;

  before(function () {
    angular.module('app',[])
      .directive('timestamp', require('../timestamp'));
  });

  beforeEach(function () {
    clock = sinon.useFakeTimers();
    fakeTime = {
      toFuzzyString: sinon.stub().returns('a while ago'),
      decayingInterval: function () {},
    };

    angular.mock.module('app', {
      time: fakeTime,
    });
  });

  afterEach(function() {
    clock.restore();
  });

  describe('#relativeTimestamp', function() {
    it('displays a relative time string', function() {
      var element = util.createDirective(document, 'timestamp', {
        timestamp: '2016-06-10T10:04:04.939Z',
      });
      assert.equal(element.ctrl.relativeTimestamp, 'a while ago');
    });

    it('is updated when the timestamp changes', function () {
      var element = util.createDirective(document, 'timestamp', {
        timestamp: '1776-07-04T10:04:04.939Z',
      });
      element.scope.timestamp = '1863-11-19T12:00:00.939Z';
      fakeTime.toFuzzyString.returns('four score and seven years ago');
      element.scope.$digest();
      assert.equal(element.ctrl.relativeTimestamp, 'four score and seven years ago');
    });

    it('is updated after time passes', function() {
      fakeTime.decayingInterval = function (date, callback) {
        setTimeout(callback, 10);
      };
      var element = util.createDirective(document, 'timestamp', {
        timestamp: '2016-06-10T10:04:04.939Z',
      });
      fakeTime.toFuzzyString.returns('60 jiffies');
      element.scope.$digest();
      clock.tick(1000);
      assert.equal(element.ctrl.relativeTimestamp, '60 jiffies');
    });

    it('is no longer updated after the component is destroyed', function() {
      var cancelRefresh = sinon.stub();
      fakeTime.decayingInterval = function () {
        return cancelRefresh;
      };
      var element = util.createDirective(document, 'timestamp', {
        timestamp: '2016-06-10T10:04:04.939Z',
      });
      element.ctrl.$onDestroy();
      assert.called(cancelRefresh);
    });
  });

  describe('#absoluteTimestamp', function () {
    it('displays the current time', function () {
      var expectedDate = new Date('2016-06-10T10:04:04.939Z');
      var element = util.createDirective(document, 'timestamp', {
        timestamp: expectedDate.toISOString(),
      });

      // The exact format of the result will depend on the current locale,
      // but check that at least the current year and time are present
      assert.match(element.ctrl.absoluteTimestamp, new RegExp('.*2016.*' +
        expectedDate.toLocaleTimeString()));
    });
  });
});
