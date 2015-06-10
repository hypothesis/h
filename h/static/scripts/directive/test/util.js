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
 *   },
 *   'Hello, world!');
 *
 * Will generate '<my-component attr-a="attrA">Hello, world!</my-component>' and
 * compile and link it with the scope:
 *
 *  { attrA: 'initial-value', scopeProperty: scopeValue }
 *
 * @param {Document} document - The DOM Document to create the element in
 * @param {string} name - The name of the directive to instantiate
 * @param {Object} [attrs] - A map of attribute names (in camelCase) to initial
 *                           values.
 * @param {Object} [initialScope] - A dictionary of properties to set on the
 *                                  scope when the element is linked
 * @param {string} [initialHtml] - Initial inner HTML content for the directive
 *                                 element.
 *
 * @return {DOMElement} The Angular jqLite-wrapped DOM element for the component.
 *                      The returned object has a link(scope) method which will
 *                      re-link the component with new properties.
 */
function createDirective(document, name, attrs, initialScope, initialHtml) {
  attrs = attrs || {};
  initialScope = initialScope || {};
  initialHtml = initialHtml || '';

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
  templateElement.innerHTML = initialHtml;

  // setup initial scope
  Object.keys(attrs).forEach(function (key) {
    $scope[key] = attrs[key];
  });

  // compile the template
  var linkFn = $compile(templateElement);

  // link the component, passing in the initial
  // scope values. The caller can then re-render/link
  // the template passing in different properties
  // and verify the output
  var linkDirective = function(props) {
    var childScope = $scope.$new();
    angular.extend(childScope, props);
    var element = linkFn(childScope);
    element.link = linkDirective;
    element.scope = childScope;
    childScope.$digest();
    return element;
  }

  return linkDirective(initialScope);
}

module.exports = {
  createDirective: createDirective
};
