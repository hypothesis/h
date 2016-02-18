'use strict';

/**
 * Converts a camelCase name into hyphenated ('camel-case') form.
 *
 * This matches how Angular maps directive names to HTML tag names.
 */
function hyphenate(name) {
  var uppercasePattern = /([A-Z])/g;
  return name.replace(uppercasePattern, '-$1').toLowerCase();
}

/**
 * Helper for retrieving an Angular module in a test.
 *
 * Given the 'inject' function from the 'angular-mocks' module,
 * retrieves an instance of the specified Angular module.
 */
function ngModule(inject, name) {
  var module;
  var helper = function (_module) {
    module = _module;
  };

  // Tell Angular which module we want using $inject
  // annotations. These take priority over function argument names.
  helper.$inject = [name];

  // inject() creates a new 'angular.$injector' service instance
  // for the current test, if one has not already been created and then
  // calls the passed function, injecting the modules it depends upon.
  inject(helper);

  return module;
}

/**
 * A helper for instantiating an AngularJS directive in a unit test.
 *
 * Usage:
 *   var domElement = createDirective(document, 'myComponent', {
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
 * The initial value may be a callback function to invoke. eg:
 *
 * var domElement = createDirective(document, 'myComponent', {
 *  onEvent: function () {
 *    console.log('event triggered');
 *  }
 * });
 *
 * If the callback accepts named arguments, these need to be specified
 * via an object with 'args' and 'callback' properties:
 *
 * var domElement = createDirective(document, 'myComponent', {
 *   onEvent: {
 *     args: ['arg1'],
 *     callback: function (arg1) {
 *       console.log('callback called with arg', arg1);
 *     }
 *   }
 * });
 *
 * @param {Document} document - The DOM Document to create the element in
 * @param {string} name - The name of the directive to instantiate
 * @param {Object} [attrs] - A map of attribute names (in camelCase) to initial
 *                           values.
 * @param {Object} [initialScope] - A dictionary of properties to set on the
 *                                  scope when the element is linked
 * @param {string} [initialHtml] - Initial inner HTML content for the directive
 *                                 element.
 * @param {Object} [opts] - Object specifying options for creating the
 *                          directive:
 *                          'parentElement' - The parent element for the new
 *                                            directive. Defaults to document.body
 *
 * @return {DOMElement} The Angular jqLite-wrapped DOM element for the component.
 *                      The returned object has a link(scope) method which will
 *                      re-link the component with new properties.
 */
function createDirective(document, name, attrs, initialScope, initialHtml, opts) {
  attrs = attrs || {};
  initialScope = initialScope || {};
  initialHtml = initialHtml || '';
  opts = opts || {};
  opts.parentElement = opts.parentElement || document.body;

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
    } else if (attrs[key].callback) {
      attrKey += '(' + attrs[key].args.join(',') + ')';
    }
    templateElement.setAttribute(attrName, attrKey);
  });
  templateElement.innerHTML = initialHtml;

  // add the element to the document's body so that
  // it responds to events, becomes visible, reports correct
  // values for its dimensions etc.
  opts.parentElement.appendChild(templateElement);

  // setup initial scope
  Object.keys(attrs).forEach(function (key) {
    if (attrs[key].callback) {
      $scope[key] = attrs[key].callback;
    } else {
      $scope[key] = attrs[key];
    }
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
    element.ctrl = element.controller(name);
    return element;
  }

  return linkDirective(initialScope);
}

module.exports = {
  createDirective: createDirective,
  ngModule: ngModule,
};
