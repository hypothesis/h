'use strict';

function ExcerptController() {
  if (this.collapse === undefined) {
    this.collapse = true;
  }

  if (this.animate === undefined) {
    this.animate = true;
  }

  if (this.enabled === undefined) {
    this.enabled = true;
  }

  this.isExpandable = function () {
    return this.overflowing && this.collapse;
  };

  this.isCollapsible = function () {
    return this.overflowing && !this.collapse;
  };

  this.toggle = function (event) {
    // When the user clicks a link explicitly to toggle the collapsed state,
    // the event is not propagated.
    event.stopPropagation();
    this.collapse = !this.collapse;
  };

  this.expand = function () {
    // When the user expands the excerpt 'implicitly' by clicking at the bottom
    // of the collapsed excerpt, the event is allowed to propagate. For
    // annotation cards, this causes clicking on a quote to scroll the view to
    // the selected annotation.
    this.collapse = false;
  };

  this.showInlineControls = function () {
    return this.overflowing && this.inlineControls;
  };

  this.bottomShadowStyles = function () {
    return {
      'excerpt__shadow': true,
      'excerpt__shadow--transparent': this.inlineControls,
      'is-hidden': !this.isExpandable(),
    };
  };
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
      var pendingOverflowCheck = false;

      // Return the content element of the excerpt.
      // This changes when the enabled state of the excerpt changes.
      function getContentElement() {
        return elem[0].querySelector('.excerpt');
      }

      // Listen for events which might cause the size of the excerpt's
      // content to change, even if the content data has not changed.

      // This currently includes top-level window resize events and media
      // (images, iframes) within the content loading.
      elem[0].addEventListener('load', scheduleOverflowCheck,
        true /* capture. 'load' events do not bubble */);

      window.addEventListener('resize', scheduleOverflowCheck);

      /**
       * Recompute whether the excerpt's content is overflowing the collapsed
       * element.
       *
       * This check is scheduled manually in response to changes in the inputs
       * to this component and certain events to avoid excessive layout flushes
       * caused by accessing the element's size.
       */
      function recomputeOverflowState() {
        if (!pendingOverflowCheck) {
          return;
        }

        pendingOverflowCheck = false;

        var contentElem = getContentElement();
        if (!contentElem) {
          return;
        }

        var overflowing = false;
        if (ctrl.enabled) {
          var hysteresisPx = ctrl.overflowHysteresis || 0;
          overflowing = contentElem.scrollHeight >
                 (ctrl.collapsedHeight + hysteresisPx);
        }
        if (overflowing === ctrl.overflowing) {
          return;
        }

        ctrl.overflowing = overflowing;
        if (ctrl.onCollapsibleChanged) {
         ctrl.onCollapsibleChanged({collapsible: ctrl.overflowing});
        }
      }

      scope.$on('$destroy', function () {
        pendingOverflowCheck = false;
        window.removeEventListener('resize', scheduleOverflowCheck);
      });

      // Schedule a deferred check of whether the content is collapsed.
      function scheduleOverflowCheck() {
        if (pendingOverflowCheck) {
          return;
        }
        pendingOverflowCheck = true;
        requestAnimationFrame(function () {
          recomputeOverflowState();
          scope.$digest();
        });
      }

      ctrl.contentStyle = function () {
        if (!ctrl.enabled) {
          return {};
        }

        var maxHeight = '';
        if (ctrl.overflowing) {
          if (ctrl.collapse) {
            maxHeight = toPx(ctrl.collapsedHeight);
          } else if (ctrl.animate) {
            // Animating the height change requires that the final
            // height be specified exactly, rather than relying on
            // auto height
            var contentElem = getContentElement();
            maxHeight = toPx(contentElem.scrollHeight);
          }
        } else if (typeof ctrl.overflowing === 'undefined' &&
                   ctrl.collapse) {
          // If the excerpt is collapsed but the overflowing state has not yet
          // been computed then the exact max height is unknown, but it will be
          // in the range [ctrl.collapsedHeight, ctrl.collapsedHeight +
          // ctrl.overflowHysteresis]
          //
          // Here we guess that the final content height is most likely to be
          // either less than `collapsedHeight` or more than `collapsedHeight` +
          // `overflowHysteresis`, in which case it will be truncated to
          // `collapsedHeight`.
          maxHeight = toPx(ctrl.collapsedHeight);
        }

        return {
          'max-height': maxHeight,
        };
      };

      // Watch properties which may affect whether the excerpt
      // needs to be collapsed and recompute the overflow state
      scope.$watch('vm.contentData', scheduleOverflowCheck);
      scope.$watch('vm.enabled', scheduleOverflowCheck);

      // Trigger an initial calculation of the overflow state.
      //
      // This is performed asynchronously so that the content of the <excerpt>
      // has settled - ie. all Angular directives have been fully applied and
      // the DOM has stopped changing. This may take several $digest cycles.
      scheduleOverflowCheck();
    },
    scope: {
      /** Whether or not expansion should be animated. Defaults to true. */
      animate: '<?',
      /**
       * The data which is used to generate the excerpt's content.
       * When this changes, the excerpt will recompute whether the content
       * is overflowing.
       */
      contentData: '<',
      /** Whether or not truncation should be enabled */
      enabled: '<?',
      /**
       * Specifies whether controls to expand and collapse
       * the excerpt should be shown inside the <excerpt> component.
       * If false, external controls can expand/collapse the excerpt by
       * setting the 'collapse' property.
       */
      inlineControls: '<',
      /** Sets whether or not the excerpt is collapsed. */
      collapse: '=?',
      /** Called when the collapsibility of the excerpt (that is, whether or
       * not the content height exceeds the collapsed height), changes.
       */
      onCollapsibleChanged: '&?',
      /** The height of this container in pixels when collapsed.
       */
      collapsedHeight: '<',
      /**
       * The number of pixels by which the height of the excerpt's content
       * must extend beyond the collapsed height in order for truncation to
       * be activated. This prevents the 'More' link from being shown to expand
       * the excerpt if it has only been truncated by a very small amount, such
       * that expanding the excerpt would reveal no extra lines of text.
       */
      overflowHysteresis: '<?',
    },
    restrict: 'E',
    transclude: true,
    template: require('../../../templates/client/excerpt.html'),
  };
}

module.exports = {
  directive: excerpt,
  Controller: ExcerptController,
};
