'use strict';

var STORAGE_KEY = 'hypothesis.privacy';

var SHARED = 'shared';
var PRIVATE = 'private';


// Return a descriptor object for the passed group.
function describeGroup(group) {
  var type;
  if (group.public) {
    type = 'public';
  } else {
    type = 'group';
  }
  return {
    name: group.name,
    type: type
  };
}


// @ngInject
function PrivacyController($scope, localStorage) {
  this._level = null;

  /**
   * @ngdoc method
   * @name PrivacyController#level
   *
   * Returns the current privacy level descriptor.
   */
  this.level = function () {
    // If the privacy level isn't set yet, we first try and set it from the
    // annotation model
    if (this._level === null) {
      if ($scope.annotation.isPrivate()) {
        this._level = PRIVATE;
      } else if ($scope.annotation.isShared()) {
        this._level = SHARED;
      }
      // If the annotation is neither (i.e. it's new) we fall through.
    }

    // If the privacy level still isn't set, try and retrieve it from
    // localStorage, falling back to shared.
    if (this._level === null) {
      var fromStorage = localStorage.getItem(STORAGE_KEY);
      if ([SHARED, PRIVATE].indexOf(fromStorage) !== -1) {
        this._level = fromStorage;
      } else {
        this._level = SHARED;
      }
      // Since we loaded from localStorage, we need to explicitly set this so
      // that the annotation model updates.
      this.setLevel(this._level);
    }

    if (this._level === SHARED) {
      return this.shared();
    }
    return this.private();
  };

  /**
   * @ngdoc method
   * @name PrivacyController#setLevel
   *
   * @param {String} level
   *
   * Sets the current privacy level. `level` may be either 'private' or
   * 'shared'.
   */
  this.setLevel = function (level) {
    if (level === SHARED) {
      this._level = SHARED;
      $scope.annotation.setShared();
      localStorage.setItem(STORAGE_KEY, SHARED);
    } else if (level === PRIVATE) {
      this._level = PRIVATE;
      $scope.annotation.setPrivate();
      localStorage.setItem(STORAGE_KEY, PRIVATE);
    }
  };

  /**
   * @ngdoc method
   * @name PrivacyController#shared
   *
   * Returns a descriptor object for the current 'shared' privacy level.
   */
  this.shared = function () {
    return describeGroup($scope.annotation.group());
  };

  /**
   * @ngdoc method
   * @name PrivacyController#private
   *
   * Returns a descriptor object for the current 'private' privacy level.
   */
  this.private = function () {
    return {
      name: 'Only Me',
      type: 'private'
    };
  };

  return this;
}


var directive = function () {
  return {
    controller: PrivacyController,
    controllerAs: 'vm',
    link: function (scope, elem, attrs, annotation) {
      scope.annotation = annotation;
    },
    require: '^annotation',
    restrict: 'E',
    scope: {},
    templateUrl: 'privacy.html'
  };
};

module.exports = {
  directive: directive,
  Controller: PrivacyController
};
