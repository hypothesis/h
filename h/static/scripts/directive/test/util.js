'use strict';

// converts a camelCase name into hyphenated ('camel-case') form,
// as Angular does when mapping directive names to tag names in HTML
function hyphenate(name) {
  var uppercasePattern = /([A-Z])/g;
  return name.replace(uppercasePattern, '-$1').toLowerCase();
}

/**
 * A helper for instantiating an AngularJS directive in a unit test.
 *
 * Usage:
 *   var domElement = createDirective('myComponent', {
 *     attrA: 'initial-value'
 *   }, {
 *     scopePropery: scopeValue
 *   });
 *
 * Will generate '<my-component attr-a="attrA"></my-component>' and
 * compile and link it with the scope:
 *
 *  { attrA: 'initial-value', scopeProperty: scopeValue }
 *
 * Attribute values are converted to scope properties of the same
 * name as the attribute and t
 *
 * @param {Document} document - The DOM Document to create the element in
 * @param {string} name - The name of the directive to instantiate
 * @param {Object} attrs - A map of attribute names (in camelCase) to initial values.
 * @param {Object} initialScope - A dictionary of properties to set on the
 *                                scope when the element is linked
 *
 * @return {DOMElement} The Angular jqLite-wrapped DOM element for the component.
 */
function createDirective(document, name, attrs, initialScope) {
  attrs = attrs || {};
  initialScope = initialScope || {};

  // create a template consisting of a single element, the directive
  // we want to create and compile it
  var $compile;
  var $scope;
  angular.mock.inject(function (_$compile_, _$rootScope_) {
    $compile = _$compile_;
    $scope = _$rootScope_.$new();
  })
  var templateElement = document.createElement(hyphenate(name));
  Object.keys(attrs).forEach(function (key) {
    var attrName = hyphenate(key);
    var attrKey = key;
    if (typeof attrs[key] === 'function') {
      attrKey += '()';
    }
    templateElement.setAttribute(attrName, attrKey);
  });

  // setup initial scope
  Object.keys(initialScope).forEach(function (key) {
    $scope[key] = initialScope[key];
  });
  Object.keys(attrs).forEach(function (key) {
    $scope[key] = attrs[key];
  });

  // instantiate component
  var element = $compile(templateElement)($scope);
  element.scope = $scope;
  $scope.$digest();
  return element;
}

module.exports = {
  createDirective: createDirective
};
