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

/**
 * @ngdoc directive
 * @name excerpt
 * @restrict E
 * @description This directive truncates the height of its contents to a
 *              specified number of lines and provides controls for expanding
 *              and collapsing the resulting truncated element.
 */
// @ngInject
function excerpt(ExcerptOverflowMonitor) {
  return {
    bindToController: true,
    controller: ExcerptController,
    controllerAs: 'vm',
    link: function (scope, elem, attrs, ctrl) {
      var overflowMonitor = new ExcerptOverflowMonitor({
        getState: function () {
          return {
            enabled: ctrl.enabled,
            animate: ctrl.animate,
            collapsedHeight: ctrl.collapsedHeight,
            collapse: ctrl.collapse,
            overflowHysteresis: ctrl.overflowHysteresis,
          };
        },
        contentHeight: function () {
          var contentElem = elem[0].querySelector('.excerpt');
          if (!contentElem) {
            return;
          }
          return contentElem.scrollHeight;
        },
        onOverflowChanged: function (overflowing) {
          ctrl.overflowing = overflowing;
          if (ctrl.onCollapsibleChanged) {
            ctrl.onCollapsibleChanged({collapsible: overflowing});
          }
          scope.$digest();
        },
      }, window.requestAnimationFrame);

      ctrl.contentStyle = overflowMonitor.contentStyle;

      // Listen for document events which might affect whether the excerpt
      // is overflowing, even if its content has not changed.
      elem[0].addEventListener('load', overflowMonitor.check, false /* capture */);
      window.addEventListener('resize', overflowMonitor.check);
      scope.$on('$destroy', function () {
        window.removeEventListener('resize', overflowMonitor.check);
      });

      // Watch input properties which may affect the overflow state
      scope.$watch('vm.contentData', overflowMonitor.check);
      scope.$watch('vm.enabled', overflowMonitor.check);

      // Trigger an initial calculation of the overflow state.
      //
      // This is performed asynchronously so that the content of the <excerpt>
      // has settled - ie. all Angular directives have been fully applied and
      // the DOM has stopped changing. This may take several $digest cycles.
      overflowMonitor.check();
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
