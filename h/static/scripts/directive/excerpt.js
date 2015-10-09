'use strict';

function ExcerptController() {
  var collapsed = true;

  // Enabled is a test seam: overwritten in link function.
  this.enabled = function () { return true; };

  // Overflowing is a test seam: overwritten in link function.
  this.overflowing = function () { return false; };

  // Is the excerpt collapsed? True if no-one has toggled the excerpt open
  // and the element is overflowing.
  this.collapsed = function () {
    if (!collapsed) {
      return false;
    }
    return this.overflowing();
  };

  this.uncollapsed = function () {
    return !collapsed;
  };

  this.toggle = function () {
    collapsed = !collapsed;
  };

  return this;
}

/**
 * @ngdoc directive
 * @name excerpt
 * @restrict E
 * @description This directive truncates its contents to a height specified in
 *              CSS, and provides controls for expanding and collapsing the
 *              resulting truncated element. For example, with the following
 *              template HTML:
 *
 *                  <article class="post">
 *                    <excerpt>
 *                      <div class="body" ng-model="post.body"></div>
 *                    </excerpt>
 *                  </article>
 *
 *              You would need to define the allowable height of the excerpt in
 *              CSS:
 *
 *                  article.post .excerpt {
 *                    max-height: 10em;
 *                  }
 *
 *              And the excerpt directive will take care of the rest.
 *
 *              You can selectively disable truncation by providing a boolean
 *              expression to the `enabled` parameter, e.g.:
 *
 *                  <excerpt enabled="!post.inFull">...</excerpt>
 */
function excerpt() {
  return {
    controller: ExcerptController,
    controllerAs: 'vm',
    link: function (scope, elem, attrs, ctrl) {
      // Test if the transcluded element is overflowing its container. We use
      // clientHeight rather than offsetHeight because we assume you'll be using
      // this with "overflow: hidden;" (i.e. no scrollbars) and it's usually
      // much faster to calculate than offsetHeight (which includes scrollbars).
      ctrl.overflowing = function overflowing() {
        var excerpt = elem[0].querySelector('.excerpt');
        if (!excerpt) {
          return false;
        }
        return (excerpt.scrollHeight > excerpt.clientHeight);
      };

      // If the `enabled` attr was provided, we override the enabled function.
      if (attrs.enabled) {
        ctrl.enabled = scope.enabled;
      }
    },
    scope: {
      enabled: '&?',
    },
    restrict: 'E',
    transclude: true,
    templateUrl: 'excerpt.html',
  };
}

module.exports = {
  directive: excerpt,
  Controller: ExcerptController,
};
