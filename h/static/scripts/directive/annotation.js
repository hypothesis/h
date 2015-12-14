/* jshint node: true */
'use strict';

var events = require('../events');

/** Return a domainModel tags array from the given vm tags array.
 *
 * domainModel.tags and vm.form.tags use different formats.  This
 * function returns a domainModel.tags-formatted copy of the given
 * vm.form.tags-formatted array.
 *
 */
function domainModelTagsFromViewModelTags(viewModelTags) {
  return (viewModelTags || []).map(function(tag) {
    return tag.text;
  });
}

/** Return a human-readable error message for the given server error.
 *
 * @param {object} reason The error object from the server. Should have
 * `status` and, if `status` is not `0`, `statusText` and (optionally)
 * `data.reason` properties.
 *
 * @returns {string}
 */
function errorMessage(reason) {
  var message;
  if (reason.status === 0) {
    message = 'Service unreachable.';
  } else {
    message = reason.status + ' ' + reason.statusText;
    if (reason.data.reason) {
      message = message + ': ' + reason.data.reason;
    }
  }
  return message;
}

/** Extract a URI, domain and title from the given domain model object.
 *
 * @param {object} domainModel An annotation domain model object as received
 *   from the server-side API.
 * @returns {object} An object with three properties extracted from the model:
 *   uri, domain and title.
 *
 */
function extractDocumentMetadata(domainModel) {
  var document_;
  var uri = domainModel.uri;
  var domain = new URL(uri).hostname;
  if (domainModel.document) {
    if (uri.indexOf('urn') === 0) {
      var i;
      for (i = 0; i < domainModel.document.link.length; i++) {
        var link = domainModel.document.link[i];
        if (link.href.indexOf('urn:') === 0) {
          continue;
        }
        uri = link.href;
        break;
      }
    }

    var documentTitle;
    if (Array.isArray(domainModel.document.title)) {
      documentTitle = domainModel.document.title[0];
    } else {
      documentTitle = domainModel.document.title;
    }

    document_ = {
      uri: uri,
      domain: domain,
      title: documentTitle || domain
    };
  } else {
    document_ = {
      uri: uri,
      domain: domain,
      title: domain
    };
  }

  if (document_.title.length > 30) {
    document_.title = document_.title.slice(0, 30) + '…';
  }

  return document_;
}

/** Return `true` if the given annotation is a reply, `false` otherwise. */
function isReply(domainModel) {
  return (domainModel.references || []).length > 0;
}

/** Return `true` if the given annotation is new, `false` otherwise.
 *
 * "New" means this annotation has been newly created client-side and not
 * saved to the server yet.
 */
function isNew(domainModel) {
  return !domainModel.id;
}

/** Restore unsaved changes to this annotation from the drafts service.
 *
 * If there are no draft changes to this annotation, does nothing.
 *
 */
function restoreFromDrafts(drafts, domainModel, vm) {
  var draft = drafts.get(domainModel);
  if (draft) {
    vm.isPrivate = draft.isPrivate;
    vm.form.tags = draft.tags;
    vm.form.text = draft.text;
  }
}

/**
  * Save the given annotation to the drafts service.
  *
  * Any existing drafts for this annotation will be overwritten.
  *
  * @param {object} drafts - The drafts service
  * @param {object} domainModel - The full domainModel object of the
  *   annotation to be saved. This full domainModel model is not retrieved
  *   again from drafts, it's only used to identify the annotation's draft in
  *   order to retrieve the fields below.
  * @param {object} vm - The view model object containing the user's unsaved
  *   changes to the annotation.
  *
  */
function saveToDrafts(drafts, domainModel, vm) {
  drafts.update(
    domainModel,
    {
      isPrivate: vm.isPrivate,
      tags: vm.form.tags,
      text: vm.form.text,
    });
}

/** Update domainModel from vm.
 *
 * Copy any properties from vm that might have been modified by the user into
 * domainModel, overwriting any existing properties in domainModel.
 *
 * Additionally, the `tags` property of vm - an array of objects each with a
 * `text` string - will become a simple array of strings in domainModel.
 *
 * @param {object} domainModel The object to copy properties to
 * @param {object} vm The object to copy properties from
 *
 */
function updateDomainModel(domainModel, vm, permissions, groups) {
  domainModel.text = vm.form.text;
  domainModel.tags = domainModelTagsFromViewModelTags(vm.form.tags);
  if (vm.isPrivate) {
    domainModel.permissions = permissions.private();
  } else {
    domainModel.permissions = permissions.shared(domainModel.group);
  }
  domainModel.group = groups.focused().id;
}

/** Update the view model from the domain model changes. */
function updateViewModel(domainModel, vm, permissions) {
  // Extend the view model with a copy of the domain model.
  // Note that copy is used so that deep properties aren't shared.
  vm.form = {
    text: domainModel.text,
    tags: viewModelTagsFromDomainModelTags(domainModel.tags),
  };
  vm.annotationURI = new URL('/a/' + domainModel.id, vm.baseURI).href;
  vm.isPrivate = permissions.isPrivate(
    domainModel.permissions, domainModel.user);
}

/** Return truthy if the given annotation is valid, falsy otherwise.
 *
* A public annotation has to have some text and/or some tags to be valid,
* public annotations with no text or tags (i.e. public highlights) are not
* valid.
*
* Non-public annotations just need to have a target to be valid, non-public
* highlights are valid.
*
* @param {object} annotation The annotation to be validated
*
*/
function validate(domainModel) {
  if (!angular.isObject(domainModel)) {
    return;
  }

  var permissions = domainModel.permissions || {};
  var readPermissions = permissions.read || [];
  var targets = domainModel.target || [];

  if (domainModel.tags && domainModel.tags.length) {
    return domainModel.tags.length;
  }

  if (domainModel.text && domainModel.text.length) {
    return domainModel.text.length;
  }

  var worldReadable = false;
  if (readPermissions.indexOf('group:__world__') !== -1) {
    worldReadable = true;
  }

  return (targets.length && !worldReadable);
}

/** Return a vm tags array from the given domainModel tags array.
 *
 * domainModel.tags and vm.form.tags use different formats.  This
 * function returns a vm.form.tags-formatted copy of the given
 * domainModel.tags-formatted array.
 *
 */
function viewModelTagsFromDomainModelTags(domainModelTags) {
  return (domainModelTags || []).map(function(tag) {
    return {text: tag};
  });
}

/**
  * @ngdoc type
  * @name annotation.AnnotationController
  *
  */
// @ngInject
function AnnotationController(
  $document, $q, $rootScope, $scope, $timeout, $window, annotationUI,
  annotationMapper, drafts, flash, features, groups, permissions, session,
  tags, time) {

  var vm = this;
  var domainModel;
  var newlyCreatedByHighlightButton;

  /**
    * Initialize this AnnotationController instance.
    *
    * Initialize the `vm` object and any other variables that it needs,
    * register event listeners, etc.
    *
    * All initialization code intended to run when a new AnnotationController
    * instance is instantiated should go into this function, except defining
    * methods on `vm`. This function is called on AnnotationController
    * instantiation after all of the methods have been defined on `vm`, so it
    * can call the methods.
    */
  function init() {
    /** The currently active action - 'view', 'create' or 'edit'. */
    vm.action = 'view';

    /** vm.form is the read-write part of vm for the templates: it contains
     *  the variables that the templates will write changes to via ng-model. */
    vm.form = {};

    // The remaining properties on vm are read-only properties for the
    // templates.

    /** The baseURI for the website, e.g. 'https://hypothes.is/'. */
    vm.baseURI = $document.prop('baseURI');

    /** Give the template access to the feature flags. */
    vm.feature = features.flagEnabled;

    /** Whether or not this annotation is private. */
    vm.isPrivate = false;

    /** Copy isSidebar from $scope onto vm for consistency (we want this
      * directive's templates to always access variables from vm rather than
      * directly from scope). */
    vm.isSidebar = $scope.isSidebar;

    /** A "fuzzy string" representation of the annotation's last updated time.
     */
    vm.timestamp = null;

    /** The domain model, contains the currently saved version of the
      * annotation from the server (or in the case of new annotations that
      * haven't been saved yet - the data that will be saved to the server when
      * they are saved).
      */
    domainModel = $scope.annotationGet();

    /**
      * `true` if this AnnotationController instance was created as a result of
      * the highlight button being clicked.
      *
      * `false` if the annotation button was clicked, or if this is a highlight
      * or annotation that was fetched from the server (as opposed to created
      * new client-side).
      */
    newlyCreatedByHighlightButton = domainModel.$highlight || false;

    // Call `onAnnotationUpdated()` whenever the "annotationUpdated" event is
    // emitted. This event is emitted after changes to the annotation are
    // successfully saved to the server, and also when changes to the
    // annotation made by another client are received by this client from the
    // server.
    $rootScope.$on('annotationUpdated', onAnnotationUpdated);

    // Call `onDestroy()` when this AnnotationController's scope is removed.
    $scope.$on('$destroy', onDestroy);

    // Call `onGroupFocused()` whenever the currently-focused group changes.
    $scope.$on(events.GROUP_FOCUSED, onGroupFocused);

    // Call `onUserChanged()` whenever the user logs in or out.
    $scope.$on(events.USER_CHANGED, onUserChanged);

    // New annotations (just created locally by the client, rather then
    // received from the server) have some fields missing. Add them.
    domainModel.user = domainModel.user || session.state.userid;
    domainModel.group = domainModel.group || groups.focused().id;
    if (!domainModel.permissions) {
      domainModel.permissions = permissions['default'](domainModel.group);
    }

    // Automatically save new highlights to the server when they're created.
    // Note that this line also gets called when the user logs in (since
    // AnnotationController instances are re-created on login) so serves to
    // automatically save highlights that were created while logged out when you
    // log in.
    saveNewHighlight();

    updateTimestamp(true);
    updateViewModel(domainModel, vm, permissions);

    // If this annotation is not a highlight and if it's new (has just been
    // created by the annotate button) or it has edits not yet saved to the
    // server - then open the editor on AnnotationController instantiation.
    if (!newlyCreatedByHighlightButton) {
      if (isNew(domainModel) || drafts.get(domainModel)) {
        vm.edit();
      }
    }
  }

  function onAnnotationUpdated(event, updatedDomainModel) {
    updateViewModel(updatedDomainModel, vm, permissions);
  }

  function onDestroy() {
    updateTimestamp = angular.noop;
  }

  function onGroupFocused() {
    if (vm.editing()) {
      saveToDrafts(drafts, domainModel, vm);
    }
  }

  function onUserChanged(event, args) {
    // If the user creates an annotation while signed out and then signs in
    // we want those annotations to still be in the sidebar after sign in.
    // So we need to save a draft of the annotation here on sign in because
    // app.coffee / the routing code is about to destroy all the
    // AnnotationController instances and only the ones that have saved drafts
    // will be re-created.
    if (vm.editing() && session.state.userid) {
      saveToDrafts(drafts, domainModel, vm);
    }
  }

  /** Save this annotation if it's a new highlight.
   *
   * The highlight will be saved to the server if the user is logged in,
   * saved to drafts if they aren't.
   *
   * If the annotation is not new (it has already been saved to the server) or
   * is not a highlight then nothing will happen.
   *
   */
  function saveNewHighlight() {
    if (!isNew(domainModel)) {
      // Already saved.
      return;
    }

    if (!vm.isHighlight()) {
      // Not a highlight,
      return;
    }

    if (domainModel.user) {
      // User is logged in, save to server.
      // Highlights are always private.
      domainModel.permissions = permissions.private();
      domainModel.$create().then(function() {
        $rootScope.$emit('annotationCreated', domainModel);
      });
    } else {
      // User isn't logged in, save to drafts.
      saveToDrafts(drafts, domainModel, vm);
    }
  }

  // We use `var foo = function() {...}` here instead of `function foo() {...}`
  // because updateTimestamp gets redefined later on.
  var updateTimestamp = function(repeat) {
    repeat = repeat || false;

    // New (not yet saved to the server) annotations don't have any .updated
    // yet, so we can't update their timestamp.
    if (!domainModel.updated) {
      return;
    }

    vm.timestamp = time.toFuzzyString(domainModel.updated);

    if (!repeat) {
      return;
    }

    var fuzzyUpdate = time.nextFuzzyUpdate(domainModel.updated);
    var nextUpdate = (1000 * fuzzyUpdate) + 500;

    $timeout(function() {
      updateTimestamp(true);
      $scope.$digest();
    }, nextUpdate, false);
  };

  /** Switches the view to a viewer, closing the editor controls if they're
   *  open.
    * @name annotation.AnnotationController#view
    */
  function view() {
    vm.action = 'view';
  }

  /**
    * @ngdoc method
    * @name annotation.AnnotationController#authorize
    * @param {string} action The action to authorize.
    * @returns {boolean} True if the action is authorized for the current user.
    * @description Checks whether the current user can perform an action on
    * the annotation.
    */
  vm.authorize = function(action) {
    // TODO: this should use auth instead of permissions but we might need
    // an auth cache or the JWT -> userid decoding might start to be a
    // performance bottleneck and we would need to get the id token into the
    // session, which we should probably do anyway (and move to opaque bearer
    // tokens for the access token).
    return permissions.permits(action, domainModel, session.state.userid);
  };

  /**
    * @ngdoc method
    * @name annotation.AnnotationController#delete
    * @description Deletes the annotation.
    */
  vm['delete'] = function() {
    return $timeout(function() {  // Don't use confirm inside the digest cycle.
      var msg = 'Are you sure you want to delete this annotation?';
      if ($window.confirm(msg)) {
        var onRejected = function(reason) {
          flash.error(
            errorMessage(reason), 'Deleting annotation failed');
        };
        $scope.$apply(function() {
          annotationMapper.deleteAnnotation(domainModel).then(
            null, onRejected);
        });
      }
    }, true);
  };

  /** Return some metadata extracted from the annotated document. */
  vm.document = function() {
    return extractDocumentMetadata(domainModel);
  };

  /**
    * @ngdoc method
    * @name annotation.AnnotationController#edit
    * @description Switches the view to an editor.
    */
  vm.edit = function() {
    restoreFromDrafts(drafts, domainModel, vm);
    vm.action = isNew(domainModel) ? 'create' : 'edit';
  };

  /**
   * @ngdoc method
   * @name annotation.AnnotationController#editing.
   * @returns {boolean} `true` if this annotation is currently being edited
   *   (i.e. the annotation editor form should be open), `false` otherwise.
   */
  vm.editing = function() {
    if (vm.action === 'create' || vm.action === 'edit') {
      return true;
    } else {
      return false;
    }
  };

  /**
    * @ngdoc method
    * @name annotation.AnnotationController#group.
    * @returns {Object} The full group object associated with the annotation.
    */
  vm.group = function() {
    return groups.focused();
  };

  /**
    * @ngdoc method
    * @name annotation.AnnotaitonController#hasContent
    * @returns {boolean} `true` if this annotation has content, `false`
    *   otherwise.
    */
  vm.hasContent = function() {
    var textLength = (vm.form.text || '').length;
    var tagsLength = (vm.form.tags || []).length;
    return (textLength > 0 || tagsLength > 0);
  };

  /**
    * @returns {boolean} True if this annotation has quotes
    */
  vm.hasQuotes = function() {
    return domainModel.target.some(function(target) {
      return target.selector && target.selector.some(function(selector) {
        return selector.type === 'TextQuoteSelector';
      });
    });
  };

  vm.id = function() {
    return domainModel.id;
  };

  /**
    * @ngdoc method
    * @name annotation.AnnotationController#isHighlight.
    * @returns {boolean} true if the annotation is a highlight, false otherwise
    */
  vm.isHighlight = function() {
    if (newlyCreatedByHighlightButton) {
      return true;
    } else if (isNew(domainModel)) {
      return false;
    } else {
      // Once an annotation has been saved to the server there's no longer a
      // simple property that says whether it's a highlight or not.  For
      // example there's no domainModel.highlight: true.  Instead a highlight is
      // defined as an annotation that isn't a page note or a reply and that
      // has no text or tags.
      var isPageNote = (domainModel.target || []).length === 0;
      return (!isPageNote && !isReply(domainModel) && !vm.hasContent());
    }
  };

  /**
    * @ngdoc method
    * @name annotation.AnnotationController#isShared
    * @returns {boolean} True if the annotation is shared (either with the
    * current group or with everyone).
    */
  vm.isShared = function() {
    return !vm.isPrivate;
  };

  // Save on Meta + Enter or Ctrl + Enter.
  vm.onKeydown = function(event) {
    if (event.keyCode === 13 && (event.metaKey || event.ctrlKey)) {
      event.preventDefault();
      vm.save();
    }
  };

  /**
    * @ngdoc method
    * @name annotation.AnnotationController#reply
    * @description
    * Creates a new message in reply to this annotation.
    */
  vm.reply = function() {
    var references = domainModel.references || [];

    // TODO: Remove this check once we have server-side code to ensure that
    // references is always an array of strings.
    if (typeof references === 'string') {
      references = [references];
    }

    references = references.concat(domainModel.id);

    var reply = annotationMapper.createAnnotation({
      references: references,
      uri: domainModel.uri
    });
    reply.group = domainModel.group;

    if (session.state.userid) {
      if (vm.isPrivate) {
        reply.permissions = permissions.private();
      } else {
        reply.permissions = permissions.shared(reply.group);
      }
    }
  };

  /**
    * @ngdoc method
    * @name annotation.AnnotationController#revert
    * @description Reverts an edit in progress and returns to the viewer.
    */
  vm.revert = function() {
    drafts.remove(domainModel);
    if (vm.action === 'create') {
      $rootScope.$emit('annotationDeleted', domainModel);
    } else {
      updateViewModel(domainModel, vm, permissions);
      view();
    }
  };

  /**
    * @ngdoc method
    * @name annotation.AnnotationController#save
    * @description Saves any edits and returns to the viewer.
    */
  vm.save = function() {
    if (!domainModel.user) {
      return flash.info('Please sign in to save your annotations.');
    }

    // Update stored tags with the new tags of this annotation.
    var newTags = vm.form.tags.filter(function(tag) {
      var tags = domainModel.tags || [];
      return tags.indexOf(tag.text) === -1;
    });
    tags.store(newTags);

    switch (vm.action) {
      case 'create':
        updateDomainModel(domainModel, vm, permissions, groups);

        if (!validate(domainModel)) {
          return flash.info('Please add text or a tag before publishing.');
        }

        var onFulfilled = function() {
          $rootScope.$emit('annotationCreated', domainModel);
          updateViewModel(domainModel, vm, permissions);
          view();
          drafts.remove(domainModel);
        };
        var onRejected = function(reason) {
          flash.error(
            errorMessage(reason), 'Saving annotation failed');
        };
        return domainModel.$create().then(onFulfilled, onRejected);

      case 'edit':
        var updatedModel = angular.copy(domainModel);
        updateDomainModel(updatedModel, vm, permissions, groups);

        if (!validate(updatedModel)) {
          return flash.info('Please add text or a tag before publishing.');
        }

        onFulfilled = function() {
          $rootScope.$emit('annotationUpdated', updatedModel);
          view();
          drafts.remove(domainModel);
        };
        onRejected = function(reason) {
          flash.error(
            errorMessage(reason), 'Saving annotation failed');
        };
        return updatedModel.$update({
          id: updatedModel.id
        }).then(onFulfilled, onRejected);
    }
  };

  /**
    * @ngdoc method
    * @name annotation.AnnotationController#setPrivacy
    *
    * Set the privacy settings on the annotation to a predefined
    * level. The supported levels are 'private' which makes the annotation
    * visible only to its creator and 'shared' which makes the annotation
    * visible to everyone in the group.
    *
    * The changes take effect when the annotation is saved
    */
  vm.setPrivacy = function(privacy) {
    // When the user changes the privacy level of an annotation they're
    // creating or editing, we cache that and use the same privacy level the
    // next time they create an annotation.
    // But _don't_ cache it when they change the privacy level of a reply.
    if (!isReply(domainModel)) {
      permissions.setDefault(privacy);
    }
    vm.isPrivate = (privacy === 'private');
  };

  vm.share = function(event) {
    var $container = angular.element(event.currentTarget).parent();
    $container.addClass('open').find('input').focus().select();

    // We have to stop propagation here otherwise this click event will
    // re-close the share dialog immediately.
    event.stopPropagation();

    $document.one('click', function() {
      $container.removeClass('open');
    });
  };

  /**
    * @ngdoc method
    * @name annotation.AnnotationController#tagsAutoComplete.
    * @returns {Promise} immediately resolved to {string[]} -
    * the tags to show in autocomplete.
    */
  vm.tagsAutoComplete = function(query) {
    return $q.when(tags.filter(query));
  };

  vm.target = function() {
    return domainModel.target;
  };

  vm.updated = function() {
    return domainModel.updated;
  };

  vm.user = function() {
    return domainModel.user;
  };

  init();
}

/**
  * @ngdoc directive
  * @name annotation
  * @restrict A
  * @description
  * Directive that instantiates
  * {@link annotation.AnnotationController AnnotationController}.
  *
  */
// @ngInject
function annotation($document) {
  function linkFn(scope, elem, attrs, controllers) {
    var ctrl = controllers[0];
    var thread = controllers[1];
    var threadFilter = controllers[2];
    var counter = controllers[3];

    elem.on('keydown', ctrl.onKeydown);

    // FIXME: Replace this counting code with something more sane, and
    // something that doesn't involve so much untested logic in the link
    // function (as opposed to unit-tested methods on the AnnotationController,
    // for example).
    // Keep track of edits going on in the thread.
    if (counter !== null) {
      // Expand the thread if descendants are editing.
      scope.$watch((function() {
        counter.count('edit');
      }), function(count) {
        if (count && !ctrl.editing && thread.collapsed) {
          thread.toggleCollapsed();
        }
      });

      // Propagate changes through the counters.
      scope.$watch((function() {return ctrl.editing;}), function(editing, old) {
        if (editing) {
          counter.count('edit', 1);
          // Disable the filter and freeze it to always match while editing.
          if ((thread !== null) && (threadFilter !== null)) {
            threadFilter.active(false);
            threadFilter.freeze(true);
          }
        } else if (old) {
          counter.count('edit', -1);
          if (threadFilter) {
            threadFilter.freeze(false);
          }
        }
      });

      // Clean up when the thread is destroyed.
      scope.$on('$destroy', function() {
        if (ctrl.editing && counter) {
          counter.count('edit', -1);
        }
      });
    }
  }

  return {
    controller: AnnotationController,
    controllerAs: 'vm',
    link: linkFn,
    require: ['annotation', '?^thread', '?^threadFilter', '?^deepCount'],
    scope: {
      annotationGet: '&annotation',
      // Indicates whether this is the last reply in a thread.
      isLastReply: '=',
      replyCount: '@annotationReplyCount',
      replyCountClick: '&annotationReplyCountClick',
      showReplyCount: '@annotationShowReplyCount',
      isSidebar: '='
    },
    templateUrl: 'annotation.html'
  };
}

module.exports = {
  // These private helper functions aren't meant to be part of the public
  // interface of this module. They've been exported temporarily to enable them
  // to be unit tested.
  // FIXME: The code should be refactored to enable unit testing without having
  // to do this.
  extractDocumentMetadata: extractDocumentMetadata,
  updateDomainModel: updateDomainModel,
  validate: validate,

  // These are meant to be the public API of this module.
  directive: annotation,
  Controller: AnnotationController
};
