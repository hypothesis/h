'use strict';

function toPx(val) {
  return val.toString() + 'px';
}

/**
 * Interface used by ExcerptOverflowMonitor to retrieve the state of the
 * <excerpt> and report when the state changes.
 *
 * interface Excerpt {
 *   getState(): State;
 *   contentHeight(): number | undefined;
 *   onOverflowChanged(): void;
 * }
 */

/**
 * A helper for the <excerpt> component which handles determinination of the
 * overflow state and content styling given the current state of the component
 * and the height of its contents.
 *
 * When the state of the excerpt or its content changes, the component should
 * call check() to schedule an async update of the overflow state.
 *
 * @param {Excerpt} excerpt - Interface used to query the current state of the
 *        excerpt and notify it when the overflow state changes.
 * @param {(callback) => number} requestAnimationFrame -
 *        Function called to schedule an async recalculation of the overflow
 *        state.
 */
function ExcerptOverflowMonitor(excerpt, requestAnimationFrame) {
  var pendingUpdate = false;

  // Last-calculated overflow state
  var prevOverflowing;

  function update() {
    var state = excerpt.getState();

    if (!pendingUpdate) {
      return;
    }

    pendingUpdate = false;

    var overflowing = false;
    if (state.enabled) {
      var hysteresisPx = state.overflowHysteresis || 0;
      overflowing = excerpt.contentHeight() >
        (state.collapsedHeight + hysteresisPx);
    }
    if (overflowing === prevOverflowing) {
      return;
    }

    prevOverflowing = overflowing;
    excerpt.onOverflowChanged(overflowing);
  }

  /**
   * Schedule a deferred check of whether the content is collapsed.
   */
  function check() {
    if (pendingUpdate) {
      return;
    }
    pendingUpdate = true;
    requestAnimationFrame(update);
  }

  /**
   * Returns an object mapping CSS properties to values that should be applied
   * to an excerpt's content element in order to truncate it based on the
   * current overflow state.
   */
  function contentStyle() {
    var state = excerpt.getState();
    if (!state.enabled) {
      return {};
    }

    var maxHeight = '';
    if (prevOverflowing) {
      if (state.collapse) {
        maxHeight = toPx(state.collapsedHeight);
      } else if (state.animate) {
        // Animating the height change requires that the final
        // height be specified exactly, rather than relying on
        // auto height
        maxHeight = toPx(excerpt.contentHeight());
      }
    } else if (typeof prevOverflowing === 'undefined' &&
               state.collapse) {
      // If the excerpt is collapsed but the overflowing state has not yet
      // been computed then the exact max height is unknown, but it will be
      // in the range [state.collapsedHeight, state.collapsedHeight +
      // state.overflowHysteresis]
      //
      // Here we guess that the final content height is most likely to be
      // either less than `collapsedHeight` or more than `collapsedHeight` +
      // `overflowHysteresis`, in which case it will be truncated to
      // `collapsedHeight`.
      maxHeight = toPx(state.collapsedHeight);
    }

    return {
      'max-height': maxHeight,
    };
  }

  this.contentStyle = contentStyle;
  this.check = check;
}

module.exports = ExcerptOverflowMonitor;
