'use strict';

function ExcerptController() {
  if (this.collapse === undefined) {
    this.collapse = true;
  }

  if (this.animate === undefined) {
    this.animate = true;
  }

  this.enabled = this.enabled || function () {
    return true;
  };

  this.isExpandable = function () {
    return this.overflowing() && this.collapse;
  };

  this.isCollapsible = function () {
    return this.overflowing() && !this.collapse;
  };

  this.toggle = function () {
    this.collapse = !this.collapse;
  };

  this.showInlineControls = function () {
    return this.overflowing() && this.inlineControls;
  }

  this.bottomShadowStyles = function () {
    return {
      'excerpt__shadow': true,
      'excerpt__shadow--transparent': this.inlineControls,
      'is-hidden': !this.isExpandable(),
    };
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
function excerpt() {
  return {
    bindToController: true,
    controller: ExcerptController,
    controllerAs: 'vm',
    link: function (scope, elem, attrs, ctrl) {
      var contentElem;

      ctrl.contentStyle = function contentStyle() {
        if (!contentElem) {
          return {};
        }

        var maxHeight;
        if (ctrl.collapse) {
          maxHeight = toPx(ctrl.collapsedHeight);
        } else if (ctrl.animate) {
          // animating the height change requires that the final
          // height be specified exactly, rather than relying on
          // auto height
          maxHeight = toPx(contentElem.scrollHeight);
        } else {
          maxHeight = '';
        }

        return {
          'max-height': maxHeight,
        };
      }

      ctrl.overflowing = function overflowing() {
        if (!contentElem) {
          return false;
        }
        return contentElem.scrollHeight > ctrl.collapsedHeight;
      };

      scope.$watch('vm.enabled()', function (isEnabled) {
        if (isEnabled) {
          contentElem = elem[0].querySelector('.excerpt');

          // trigger an update of the excerpt when events happen
          // outside of Angular's knowledge that might affect the content
          // size. For now, the only event we handle is loading of
          // embedded media or frames
          contentElem.addEventListener('load', scope.$digest.bind(scope),
            true /* capture. 'load' events do not bubble */);
        } else {
          contentElem = undefined;
        }
      });

      scope.$watch('vm.overflowing()', function () {
        if (ctrl.onCollapsibleChanged) {
          ctrl.onCollapsibleChanged({collapsible: ctrl.overflowing()});
        }
      });
    },
    scope: {
      /** Whether or not expansion should be animated. Defaults to true. */
      animate: '=',
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
      onCollapsibleChanged: '&?',
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
