/* jshint node: true */
'use strict';

var events = require('../events');

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
 * @param {object} model An annotation domain model object as received from the
 *   server-side API.
 * @returns {object} An object with three properties extracted from the model:
 *   uri, domain and title.
 *
 */
function extractDocumentMetadata(model) {
  var document_;
  var uri = model.uri;
  var domain = new URL(uri).hostname;
  if (model.document) {
    if (uri.indexOf('urn') === 0) {
      var i;
      for (i = 0; i < model.document.link.length; i++) {
        var link = model.document.link[i];
        if (link.href.indexOf('urn:') === 0) {
          continue;
        }
        uri = link.href;
        break;
      }
    }

    var documentTitle = Array.isArray(
      model.document.title) ? model.document.title[0] : model.document.title;

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

/** Copy properties from viewModel into domainModel.
*
* All top-level properties in viewModel will be copied into domainModel,
* overwriting any existing properties with the same keys in domainModel.
*
* Additionally, the `tags` property of viewModel - an array of objects
* each with a `text` string - will become a simple array of strings in
* domainModel.
*
* @param {object} domainModel The object to copy properties to
* @param {object} viewModel The object to copy properties from
* @returns undefined
*
*/
function updateDomainModel(domainModel, viewModel) {
  angular.extend(domainModel, viewModel);
  domainModel.tags = viewModel.tags.map(function(tag) {
    return tag.text;
  });
}

/** Update the view model from the domain model changes. */
function updateViewModel(drafts, model, vm) {
  var draft = drafts.get(model);

  // Extend the view model with a copy of the domain model.
  // Note that copy is used so that deep properties aren't shared.
  vm.annotation = angular.extend({}, angular.copy(model));

  // If we have unsaved changes to this annotation, apply them
  // to the view model.
  if (draft) {
    angular.extend(vm.annotation, angular.copy(draft));
  }

  vm.annotationURI = new URL(
    '/a/' + vm.annotation.id, vm.baseURI).href;

  vm.document = extractDocumentMetadata(model);

  // Form the tags for ngTagsInput.
  vm.annotation.tags = (vm.annotation.tags || []).map(function(tag) {
    return {text: tag};
  });
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
function validate(annotation) {
  if (!angular.isObject(annotation)) {
    return;
  }

  var permissions = annotation.permissions || {};
  var readPermissions = permissions.read || [];
  var targets = annotation.target || [];

  if (annotation.tags && annotation.tags.length) {
    return annotation.tags.length;
  }

  if (annotation.text && annotation.text.length) {
    return annotation.text.length;
  }

  var worldReadable = false;
  if (readPermissions.indexOf('group:__world__') !== -1) {
    worldReadable = true;
  }

  return (targets.length && !worldReadable);
}

/**
  * `AnnotationController` provides an API for the annotation directive. It
  * manages the interaction between the domain and view models and uses the
  * {@link annotationMapper AnnotationMapper service} for persistence.
  *
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
  var model;
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

    /** The view model, contains user changes to the annotation that haven't
      * been saved to the server yet. */
    vm.annotation = {};

    /** The baseURI for the website, e.g. 'https://hypothes.is/'. */
    vm.baseURI = $document.prop('baseURI');

    /** An object that will contain some metadata about the annotated document.
     */
    vm.document = null;

    /** Give the template access to the feature flags. */
    vm.feature = features.flagEnabled;

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
    model = $scope.annotationGet();

    /**
      * `true` if this AnnotationController instance was created as a result of
      * the highlight button being clicked.
      *
      * `false` if the annotation button was clicked, or if this is a highlight
      * or annotation that was fetched from the server (as opposed to created
      * new client-side).
      */
    newlyCreatedByHighlightButton = model.$highlight || false;

    // Call `onDestroy()` when this AnnotationController's scope is removed.
    $scope.$on('$destroy', onDestroy);

    // Call `onModelChange()` whenever `model` changes.
    $scope.$watch((function() {return model;}), onModelChange, true);

    // Call `onGroupFocused()` whenever the currently-focused group changes.
    $scope.$on(events.GROUP_FOCUSED, onGroupFocused);

    // New annotations (just created locally by the client, rather then
    // received from the server) have some fields missing. Add them.
    model.user = model.user || session.state.userid;
    model.group = model.group || groups.focused().id;
    model.permissions = model.permissions || permissions['default'](model.group);

    // Automatically save new highlights to the server when they're created.
    // Note that this line also gets called when the user logs in (since
    // AnnotationController instances are re-created on login) so serves to
    // automatically save highlights that were created while logged out when you
    // log in.
    saveNewHighlight();

    // If this annotation is not a highlight and if it's new (has just been
    // created by the annotate button) or it has edits not yet saved to the
    // server - then open the editor on AnnotationController instantiation.
    if (!newlyCreatedByHighlightButton) {
      if (!model.id || drafts.get(model)) {
        vm.edit();
      }
    }
  }

  /** Called when this AnnotationController instance's scope is removed. */
  function onDestroy() {
    updateTimestamp = angular.noop;
  }

  /** Called whenever the currently-focused group changes. */
  function onGroupFocused() {
    if (!vm.editing()) {
      return;
    }

    // Move any new annotations to the currently focused group when
    // switching groups. See GH #2689 for context.
    if (!model.id) {
      var newGroup = groups.focused().id;
      var isShared = permissions.isShared(
        vm.annotation.permissions, vm.annotation.group);
      if (isShared) {
        model.permissions = permissions.shared(newGroup);
        vm.annotation.permissions = model.permissions;
      }
      model.group = newGroup;
      vm.annotation.group = model.group;
    }

    if (drafts.get(model)) {
      var draftDomainModel = {};
      updateDomainModel(draftDomainModel, vm.annotation);
      updateDraft(draftDomainModel);
    }
  }

  /** Called whenever `model` changes. */
  function onModelChange(model, old) {
    if (model.updated !== old.updated) {
      // Discard saved drafts.
      drafts.remove(model);
    }

    updateTimestamp(model === old);  // Repeat on first run.
    updateViewModel(drafts, model, vm);
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
    if (model.id) {
      // Already saved.
      return;
    }

    if (!vm.isHighlight()) {
      // Not a highlight,
      return;
    }

    if (model.user) {
      // User is logged in, save to server.
      // Highlights are always private.
      model.permissions = permissions.private();
      model.$create().then(function() {
        $rootScope.$emit('annotationCreated', model);
      });
    } else {
      // User isn't logged in, save to drafts.
      updateDraft(model);
    }
  }

  /**
   * Create or update the existing draft for this annotation using
   * the text and tags from the domain model in `draft`.
   */
  function updateDraft(draft) {
    // Drafts only preserve the text, tags and permissions of the annotation
    // (i.e. only the bits that the user can edit), changes to other
    // properties are not preserved.
    var changes = {};
    if (draft.text) {
      changes.text = draft.text;
    }
    if (draft.tags) {
      changes.tags = draft.tags;
    }
    if (draft.permissions) {
      changes.permissions = draft.permissions;
    }
    drafts.update(model, changes);
  }

  // We use `var foo = function() {...}` here instead of `function foo() {...}`
  // because updateTimestamp gets redefined later on.
  var updateTimestamp = function(repeat) {
    repeat = repeat || false;

    // New (not yet saved to the server) annotations don't have any .updated
    // yet, so we can't update their timestamp.
    if (!model.updated) {
      return;
    }

    vm.timestamp = time.toFuzzyString(model.updated);

    if (!repeat) {
      return;
    }

    var fuzzyUpdate = time.nextFuzzyUpdate(model.updated);
    var nextUpdate = (1000 * fuzzyUpdate) + 500;

    $timeout(function() {
      updateTimestamp(true);
      $scope.$digest();
    }, nextUpdate, false);
  }

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
    return permissions.permits(action, model, session.state.userid);
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
          annotationMapper.deleteAnnotation(model).then(
            null, onRejected);
        });
      }
    }, true);
  };

  /**
    * @ngdoc method
    * @name annotation.AnnotationController#edit
    * @description Switches the view to an editor.
    */
  vm.edit = function() {
    if (!drafts.get(model)) {
      updateDraft(model);
    }
    vm.action = model.id ? 'edit' : 'create';
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
    return groups.get(model.group);
  };

  /**
    * @ngdoc method
    * @name annotation.AnnotaitonController#hasContent
    * @returns {boolean} `true` if this annotation has content, `false`
    *   otherwise.
    */
  vm.hasContent = function() {
    var textLength = (vm.annotation.text || '').length;
    var tagsLength = (vm.annotation.tags || []).length;
    return (textLength > 0 || tagsLength > 0);
  };

  /**
    * @returns {boolean} True if this annotation has quotes
    */
  vm.hasQuotes = function() {
    return vm.annotation.target.some(function(target) {
      return target.selector && target.selector.some(function(selector) {
        return selector.type === 'TextQuoteSelector';
      });
    });
  };

  /**
    * @ngdoc method
    * @name annotation.AnnotationController#isHighlight.
    * @returns {boolean} true if the annotation is a highlight, false otherwise
    */
  vm.isHighlight = function() {
    if (newlyCreatedByHighlightButton) {
      return true;
    } else if (!model.id) {
      // If an annotation has no model.id (i.e. it has not been saved to the
      // server yet) and newlyCreatedByHighlightButton is false, then it must
      // be an annotation not a highlight (even though it may not have any
      // text or tags yet).
      return false;
    } else {
      // Once an annotation has been saved to the server there's no longer a
      // simple property that says whether it's a highlight or not.  For
      // example there's no model.highlight: true.  Instead a highlight is
      // defined as an annotation that isn't a page note or a reply and that
      // has no text or tags.
      var isPageNote = (model.target || []).length === 0;
      var isReply = (model.references || []).length !== 0;
      return (!isPageNote && !isReply && !vm.hasContent());
    }
  };

  /**
    * @ngdoc method
    * @name annotation.AnnotationController#isPrivate
    * @returns {boolean} True if the annotation is private to the current user.
    */
  vm.isPrivate = function() {
    return permissions.isPrivate(vm.annotation.permissions, model.user);
  };

  /**
    * @ngdoc method
    * @name annotation.AnnotationController#isShared
    * @returns {boolean} True if the annotation is shared (either with the
    * current group or with everyone).
    */
  vm.isShared = function() {
    return permissions.isShared(vm.annotation.permissions, model.group);
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
    var id = model.id;
    var references = model.references || [];

    // TODO: Remove this check once we have server-side code to ensure that
    // references is always an array of strings.
    if (typeof references === 'string') {
      references = [references];
    }

    references = references.concat(id);

    var reply = annotationMapper.createAnnotation({
      references: references,
      uri: model.uri
    });
    reply.group = model.group;

    if (session.state.userid) {
      if (permissions.isShared(model.permissions, model.group)) {
        reply.permissions = permissions.shared(reply.group);
      } else {
        reply.permissions = permissions.private();
      }
    }
  };

  /**
    * @ngdoc method
    * @name annotation.AnnotationController#revert
    * @description Reverts an edit in progress and returns to the viewer.
    */
  vm.revert = function() {
    drafts.remove(model);
    if (vm.action === 'create') {
      $rootScope.$emit('annotationDeleted', model);
    } else {
      updateViewModel(drafts, model, vm);
      view();
    }
  };

  /**
    * @ngdoc method
    * @name annotation.AnnotationController#save
    * @description Saves any edits and returns to the viewer.
    */
  vm.save = function() {
    if (!model.user) {
      return flash.info('Please sign in to save your annotations.');
    }

    if (!validate(vm.annotation)) {
      return flash.info('Please add text or a tag before publishing.');
    }

    // Update stored tags with the new tags of this annotation.
    var newTags = vm.annotation.tags.filter(function(tag) {
      var tags = model.tags || [];
      return tags.indexOf(tag.text) === -1;
    });
    tags.store(newTags);

    switch (vm.action) {
      case 'create':
        updateDomainModel(model, vm.annotation);
        var onFulfilled = function() {
          $rootScope.$emit('annotationCreated', model);
          view();
        };
        var onRejected = function(reason) {
          flash.error(
            errorMessage(reason), 'Saving annotation failed');
        };
        return model.$create().then(onFulfilled, onRejected);

      case 'edit':
        var updatedModel = angular.copy(model);
        updateDomainModel(updatedModel, vm.annotation);
        onFulfilled = function() {
          angular.copy(updatedModel, model);
          $rootScope.$emit('annotationUpdated', model);
          view();
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
    if (!model.references) {  // If the annotation is not a reply.
      permissions.setDefault(privacy);
    }
    if (privacy === 'private') {
      vm.annotation.permissions = permissions.private();
    } else if (privacy === 'shared') {
      vm.annotation.permissions = permissions.shared(model.group);
    }
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
  updateViewModel: updateViewModel,
  updateDomainModel: updateDomainModel,
  validate: validate,

  // These are meant to be the public API of this module.
  directive: annotation,
  Controller: AnnotationController
};
