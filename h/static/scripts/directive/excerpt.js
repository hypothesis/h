'use strict';

function ExcerptController() {
  this.collapse = true;

  this.enabled = this.enabled || function () {
    return true;
  };

  // Test seam. Overwritten in the link function
  this.overflowing = function () {
    return false;
  };

  this.isExpandable = function () {
    return this.collapse && this.overflowing();
  };

  this.isCollapsible = function () {
    return !this.collapse;
  };

  this.toggle = function () {
    this.collapse = !this.collapse;
  };

  this.showInlineControls = function () {
    return this.inlineControls && (this.isExpandable() || this.isCollapsible())
  }
}

function toPx(val) {
  return val.toString() + 'px';
}

/**
 * @ngdoc directive
 * @name excerpt
 * @restrict E
 * @description This directive truncates the height of its contents to a
 *              specified number of lines and provides controls for expanding
 *              and collapsing the resulting truncated element.
 */
// @ngInject
function excerpt($timeout) {
  return {
    bindToController: true,
    controller: ExcerptController,
    controllerAs: 'vm',
    link: function (scope, elem, attrs, ctrl) {
      if (!ctrl.enabled()) {
        return;
      }

      var contentElem;
      ctrl.overflowing = function overflowing() {
        if (!contentElem) {
          return false;
        }
        return contentElem.scrollHeight > ctrl.collapsedHeight;
      };

      scope.$evalAsync(function () {
        contentElem = elem[0].querySelector('.excerpt');

        // update max height
        scope.$watch('vm.collapse', function (isCollapsed) {
          if (isCollapsed) {
            contentElem.style.maxHeight = toPx(ctrl.collapsedHeight);
          } else {
            contentElem.style.maxHeight = toPx(contentElem.scrollHeight);
          }
        });

        scope.$watch('vm.overflowing()', function () {
          if (ctrl.onCollapsibleChanged) {
            ctrl.onCollapsibleChanged({collapsible: ctrl.overflowing()});
          }
        });

        function checkForOverflowChange() {
          scope.$digest();
        }

        // trigger a recalculation of ctrl.overflowing() and properties
        // which depend upon it when embedded media loads.
        //
        // In future we might wish to trigger checking for other events
        // outside of Angular's knowledge as well, eg. loading of embedded
        // media
        contentElem.addEventListener('load', checkForOverflowChange,
          true /* capture. 'load' events do not bubble */);
      });
    },
    scope: {
      /** Whether or not truncation should be enabled */
      enabled: '&?',
      /**
       * Specifies whether controls to expand and collapse
       * the excerpt should be shown inside the <excerpt> component.
       * If false, external controls can expand/collapse the excerpt by
       * setting the 'collapse' property.
       */
      inlineControls: '=',
      /** Sets whether or not the excerpt is collapsed. */
      collapse: '=',
      /** Called when the collapsibility of the excerpt (that is, whether or
       * not the content height exceeds the collapsed height), changes.
       */
      onCollapsibleChanged: '&',
      /** The height of this container in pixels when collapsed.
       */
      collapsedHeight: '=',
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
