'use strict';

/** Default state for new threads, before applying filters etc. */
var DEFAULT_THREAD_STATE = {
  /** The Annotation which is displayed by this thread. */
  annotation: undefined,
  /** The parent Thread */
  parent: undefined,
  /** True if replies to this annotation are hidden. */
  collapsed: false,
  /** True if this annotation matches the current filters. */
  visible: true,
  /** Replies to this annotation. */
  children: [],
  /**
    * The total number of children of this annotation,
    * including any which have been hidden by filters.
    */
  totalChildren: 0,
};

/**
 * Returns a persistent identifier for an Annotation.
 * If the Annotation has been created on the server, it will have
 * an ID assigned, otherwise we fall back to the local-only '$$tag'
 * property.
 */
function id(annotation) {
  return annotation.id || annotation.$$tag;
}

/**
 * Creates a thread of annotations from a list of annotations.
 *
 * @param {Array<Annotation>} annotations - The input annotations to thread.
 * @return {Thread} - The input annotations threaded into a tree structure.
 */
function threadAnnotations(annotations) {
  // map of annotation ID -> container
  var threads = {};

  // Build mapping of annotation ID -> thread
  annotations.forEach(function (annotation) {
    threads[id(annotation)] = Object.assign({}, DEFAULT_THREAD_STATE, {
      annotation: annotation,
      children: [],
    });
  });

  // Set each thread's parent to the nearest parent which still exists
  annotations.forEach(function (annotation) {
    if (!annotation.references) {
      return;
    }

    for (var i=annotation.references.length; i >= 0; i--) {
      var parentID = annotation.references[i];
      if (!threads[parentID]) {
        // Parent does not exist, try the next one
        continue;
      }

      var grandParentID = threads[parentID].parent;
      var loop = false;
      while (grandParentID) {
        if (grandParentID === id(annotation)) {
          // Stop: We have a loop
          loop = true;
          break;
        } else {
          grandParentID = threads[grandParentID].parent;
        }
      }
      if (loop) {
        // We found a loop in the reference tree, skip this parent
        continue;
      }

      threads[id(annotation)].parent = parentID;
      threads[parentID].children.push(threads[id(annotation)]);
      break;
    }
  });

  // Collect the set of threads which have no parent as
  // children of the thread root
  var roots = [];
  Object.keys(threads).map(function (id) {
    if (!threads[id].parent) {
      // Top-level threads are collapsed by default
      threads[id].collapsed = true;
      roots.push(threads[id]);
    }
  });

  var root = {
    annotation: undefined,
    children: roots,
    visible: true,
    collapsed: false,
    totalChildren: roots.length,
  };

  return root;
}

/**
 * Returns a copy of `thread` with the thread
 * and each of its children transformed by mapFn(thread).
 *
 * @param {Thread} thread
 * @param {(Thread) => Thread} mapFn
 */
function mapThread(thread, mapFn) {
  return Object.assign({}, mapFn(thread), {
    children: thread.children.map(function (child) {
      return mapThread(child, mapFn);
    }),
  });
}

/**
 * Return a sorted copy of an array of threads.
 *
 * @param {Array<Thread>} threads - The list of threads to sort
 * @param {(Annotation,Annotation) => boolean} compareFn
 * @return {Array<Thread>} Sorted list of threads
 */
function sort(threads, compareFn) {
  return threads.slice().sort(function (a, b) {
    if (compareFn(a.annotation, b.annotation)) {
      return -1;
    } else if (compareFn(b.annotation, a.annotation)) {
      return 1;
    } else {
      return 0;
    }
  });
}

/**
 * Return a copy of `thread` with siblings sorted according
 * to `compareFn` . Sorting is non-recursive, so only the immediate children
 * of `thread` are sorted.
 */
function sortThread(thread, compareFn) {
  // Children should always be sorted by age.
  return Object.assign({}, thread, {
    children: sort(thread.children, compareFn),
  });
}

/**
 * Return a copy of @p thread with the replyCount property updated.
 */
function countReplies(thread) {
  var children = thread.children.map(countReplies);
  return Object.assign({}, thread, {
    children: children,
    replyCount: children.reduce(function (total, child) {
      return total + 1 + child.replyCount;
    }, 0),
  });
}

/** Return true if a thread has any visible children. */
function hasVisibleChildren(thread) {
  return thread.children.some(function (child) {
    return child.visible || hasVisibleChildren(child);
  });
}


function hasSelectedChildren(thread, selected) {
  return thread.children.some(function (child) {
    return selected.indexOf(id(child.annotation)) !== -1 ||
           hasSelectedChildren(child, selected);
  });
}

/**
 * Default options for buildThread()
 */
var defaultOpts = {
  /** List of currently selected annotation IDs */
  selected: [],
  /**
   * List of IDs of annotations that should be shown even if they
   * do not match the current filter.
   */
  forceVisible: undefined,
  /**
   * Predicate function that returns true if an annotation should be
   * displayed.
   */
  searchFilter: undefined,
  /**
   * Mapping of annotation IDs to expansion states.
   */
  expanded: {},
  /**
   * Less-than comparison function used to compare annotations in order to sort
   * the top-level thread.
   */
  currentSortFn: function (a, b) {
    return a.id < b.id;
  },
};

/**
 * Project, filter and sort a list of annotations into a thread structure for
 * display by the <annotation-thread> directive.
 *
 * buildThread() takes as inputs a flat list of annotations,
 * the current visibility filters and sort function and returns
 * the thread structure that should be rendered.
 *
 * @param {Array<Annotation>} annotations - A list of annotations and replies
 * @param {Options} opts
 * @return {Thread} - The root thread, whose children are the top-level
 *                    annotations to display.
 */
function buildThread(annotations, opts) {
  opts = Object.assign({}, defaultOpts, opts);

  var thread = threadAnnotations(annotations);

  // Mark annotations as visible or hidden depending on whether
  // they are being edited and whether they match the current filter
  // criteria
  var shouldShowThread = function (annotation) {
    if (opts.forceVisible && opts.forceVisible.indexOf(id(annotation)) !== -1) {
      return true;
    }
    if (opts.selected.length > 0 &&
        opts.selected.indexOf(id(annotation)) === -1) {
      return false;
    }
    if (opts.searchFilter && !opts.searchFilter(annotation)) {
      return false;
    }
    return true;
  };

  // Set the visibility of threads based on whether they match
  // the current search filter
  thread = mapThread(thread, function (thread) {
    return Object.assign({}, thread, {
      visible: thread.visible &&
               thread.annotation &&
               shouldShowThread(thread.annotation),
    });
  });

  // Expand any threads which:
  // 1) Have been explicitly expanded OR
  // 2) Have children matching the search filter OR
  // 3) Contain children which have been selected
  thread = mapThread(thread, function (thread) {
    if (!thread.annotation) {
      return thread;
    }

    var id = thread.annotation.id;

    // If the thread was explicitly expanded or collapsed,
    // respect that option
    if (opts.expanded.hasOwnProperty(id)) {
      return Object.assign({}, thread, {collapsed: !opts.expanded[id]});
    }

    var hasUnfilteredChildren = opts.searchFilter && hasVisibleChildren(thread);

    return Object.assign({}, thread, {
      collapsed: thread.collapsed &&
                 !hasUnfilteredChildren &&
                 !hasSelectedChildren(thread, opts.selected)
    });
  });

  // Remove top-level threads which contain no visible annotations
  thread.children = thread.children.filter(function (child) {
    return child.visible || hasVisibleChildren(child);
  });

  // Sort the root thread according to the current search criteria
  thread = sortThread(thread, opts.currentSortFn);

  // Update reply counts
  thread = countReplies(thread);

  return thread;
}

module.exports = buildThread;
