'use strict';

var events = require('../events');

function validate(value) {
  var permissions;
  var readPermissions;
  var worldReadable = false;
  var targets;

  if (!angular.isObject(value)) {
    return;
  }

  permissions = value.permissions || {};
  readPermissions = permissions.read || [];
  targets = value.target || [];

  if (value.tags && value.tags.length) {
    return value.tags.length;
  }

  if (value.text && value.text.length) {
    return value.text.length;
  }

  if (readPermissions.indexOf('group:__world__') !== -1) {
    worldReadable = true;
  }

  return (targets.length && !worldReadable);
}

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

// @ngInject
/**
  * @ngdoc type
  * @name annotation.AnnotationController
  *
  * @property {Object} annotation The annotation view model.
  * @property {Object} document The document metadata view model.
  * @property {string} action One of 'view', 'edit', 'create' or 'delete'.
  * @property {string} preview If previewing an edit then 'yes', else 'no'.
  * @property {boolean} editing True if editing components are shown.
  * @property {boolean} isSidebar True if we are in the sidebar (not on the
  *                               stream page or an individual annotation page)
  *
  * @description
  *
  * `AnnotationController` provides an API for the annotation directive. It
  * manages the interaction between the domain and view models and uses the
  * {@link annotationMapper AnnotationMapper service} for persistence.
  */
function AnnotationController(
  $document, $q, $rootScope, $scope, $timeout, $window, annotationUI,
  annotationMapper, drafts, flash, groups, permissions, session, tags, time) {

  var vm = this;

  var highlight;
  var isNewAnnotation;
  var model;
  var updateDomainModel;
  var updateDraft;
  var updateTimestamp;

  vm.annotation = {};
  vm.action = 'view';
  vm.document = null;
  vm.editing = false;
  vm.isSidebar = false;
  vm.preview = 'no';
  vm.timestamp = null;

  model = $scope.annotationGet();
  if (model.user === undefined) {
    model.user = session.state.userid;
  }
  if (!model.group) {
    model.group = groups.focused().id;
  }
  model.permissions = model.permissions || permissions['default'](model.group);
  highlight = model.$highlight;

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
    * @name annotation.AnnotationController#tagsAutoComplete.
    * @returns {Promise} immediately resolved to {string[]} -
    * the tags to show in autocomplete.
    */
  vm.tagsAutoComplete = function(query) {
    return $q.when(tags.filter(query));
  };

  /**
    * @ngdoc method
    * @name annotation.AnnotationController#isHighlight.
    * @returns {boolean} True if the annotation is a highlight.
    */
  vm.isHighlight = function() {
    var targetLength = (model.target || []).length;
    var referencesLength = (model.references || []).length;
    var tagsLength = (model.tags || []).length;
    return (targetLength && !referencesLength && !(model.text || tagsLength));
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
    if (!model.references) {
      permissions.setDefault(privacy);
    }
    if (privacy === 'private') {
      vm.annotation.permissions = permissions.private();
    } else if (privacy === 'shared') {
      vm.annotation.permissions = permissions.shared(model.group);
    }
  };

  /**
    * @ngdoc method
    * @name annotation.AnnotaitonController#hasContent
    * @returns {boolean} True if the currently edited annotation has
    *          content (ie. is not just a highlight)
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
    * @name annotation.AnnotationController#authorize
    * @param {string} action The action to authorize.
    * @returns {boolean} True if the action is authorized for the current user.
    * @description Checks whether the current user can perform an action on
    * the annotation.
    */
  vm.authorize = function(action) {
    if (model === null) {
      return false;
    }
    return permissions.permits(action, model, session.state.userid);
  };

  /**
    * @ngdoc method
    * @name annotation.AnnotationController#delete
    * @description Deletes the annotation.
    */
  vm['delete'] = function() {
    return $timeout(function() {
      var onRejected;
      var msg = 'Are you sure you want to delete this annotation?';
      if ($window.confirm(msg)) {
        onRejected = function(reason) {
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
    vm.action = model.id !== null ? 'edit' : 'create';
    vm.editing = true;
    vm.preview = 'no';
  };

  /**
    * @ngdoc method
    * @name annotation.AnnotationController#view
    * @description Switches the view to a viewer, closing the editor controls
    *              if they are open.
    */
  vm.view = function() {
    vm.editing = false;
    vm.action = 'view';
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
      vm.render();
      vm.view();
    }
  };

  updateDomainModel = function(domainModel, viewModel) {
    var i;
    var tagTexts = [];
    for (i = 0; i < viewModel.tags.length; i++) {
      tagTexts.concat(viewModel.tags[i].text);
    }
    angular.extend(domainModel, viewModel, {tag: tagTexts});
  };

  updateDraft = function(draft) {
    // Drafts only preserve the text, tags and permissions of the annotation
    // (i.e. only the bits that the user can edit), changes to other
    // properties are not preserved.
    drafts.update(model, {
      text: draft.text,
      tags: draft.tags,
      permissions: draft.permissions
    });
  };

  /**
    * @ngdoc method
    * @name annotation.AnnotationController#save
    * @description Saves any edits and returns to the viewer.
    */
  vm.save = function() {
    var newTags;
    var onFulfilled;
    var onRejected;
    var updatedModel;

    if (!model.user) {
      return flash.info('Please sign in to save your annotations.');
    }

    if (!validate(vm.annotation)) {
      return flash.info('Please add text or a tag before publishing.');
    }

    newTags = vm.annotation.tags.filter(function(tag) {
      var tags = model.tags || [];
      return (tags.indexOf(tag.text) === -1);
    });
    tags.store(newTags);

    switch (vm.action) {
      case 'create':
        updateDomainModel(model, vm.annotation);
        onFulfilled = function() {
          $rootScope.$emit('annotationCreated', model);
          vm.view();
        };
        onRejected = function(reason) {
          flash.error(
            errorMessage(reason), 'Saving annotation failed');
        };
        return model.$create().then(onFulfilled, onRejected);

      case 'edit':
        updatedModel = angular.copy(model);
        updateDomainModel(updatedModel, vm.annotation);
        onFulfilled = function() {
          angular.copy(updatedModel, model);
          $rootScope.$emit('annotationUpdated', model);
          vm.view();
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
    * @name annotation.AnnotationController#reply
    * @description
    * Creates a new message in reply to this annotation.
    */
  vm.reply = function() {
    var id = model.id;
    var references = model.references || [];
    var reply;
    var uri = model.uri;

    if (typeof references === 'string') {
      references = [references];
    }

    references = references.concat(id);

    reply = annotationMapper.createAnnotation({
      references: references,
      uri: uri
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
    * @name annotation.AnnotationController#render
    * @description Called to update the view when the model changes.
    */
  vm.render = function() {
    var documentTitle;
    var domain;
    var draft = drafts.get(model);
    var i;
    var link;
    var tagsAsObjects;
    var uri = model.uri;

    vm.annotation = angular.extend({}, angular.copy(model));

    if (draft) {
      angular.extend(vm.annotation, angular.copy(draft));
    }

    vm.annotationURI = new URL(
      '/a/' + vm.annotation.id, vm.baseURI).href;

    domain = new URL(uri).hostname;

    if (model.document) {
      if (uri.indexOf('urn') === 0) {
        for (i = 0; i < model.document.link.length; i++) {
          link = model.document.link[i];
          if (!(link.href.indexOf('urn'))) {
            continue;
          }
          uri = link.href;
          break;
        }
      }

      documentTitle = Array.isArray(
        model.document.title) ? model.document.title[0] : model.document.title;

      vm.document = {
        uri: uri,
        domain: domain,
        title: documentTitle || domain
      };
    } else {
      vm.document = {
        uri: uri,
        domain: domain,
        title: domain
      };
    }

    if (vm.document.title.length > 30) {
      vm.document.title = vm.document.title.slice(0, 30) + '…';
    }

    tagsAsObjects = [];
    for (i = 0; i < (vm.annotation.tags || []).length; i++) {
      tagsAsObjects[tagsAsObjects.length] = {text: vm.annotation.tags[i]};
    }
    vm.annotation.tags = tagsAsObjects;
  };

  updateTimestamp = function(repeat) {
    var fuzzyUpdate;
    var nextUpdate;

    repeat = repeat || false;

    if (!model.updated) {
      return;
    }

    vm.timestamp = time.toFuzzyString(model.updated);

    if (!repeat) {
      return;
    }

    fuzzyUpdate = time.nextFuzzyUpdate(model.updated);
    nextUpdate = (1000 * fuzzyUpdate) + 500;

    $timeout(function() {
      updateTimestamp(true);
      $scope.$digest();
    }, nextUpdate, false);
  };

  vm.baseURI = $document.prop('baseURI');

  $scope.$on('$destroy', function() {
    updateTimestamp = angular.noop;
  });

  $scope.$watch((function() {return model;}), function(model, old) {
    if (model.updated !== old.updated) {
      drafts.remove(model);
    }

    if (vm.isHighlight() && highlight) {
      if (model.user && !model.id) {
        model.permissions = permissions.private();
        model.$create().then(function() {
          $rootScope.$emit('annotationCreated', model);
        });
        highlight = false;
      } else {
        updateDraft(model);
      }
    }

    updateTimestamp(model === old);
    vm.render();
  }, true);

  $scope.$on(events.USER_CHANGED, function() {
    if (model.user === null) {
      model.user = session.state.userid;
    }
    if (!model.permissions) {
      model.permissions = permissions['default'](model.group);
    }
  });

  isNewAnnotation = !(model.id || (vm.isHighlight() && highlight));
  if (isNewAnnotation || drafts.get(model)) {
    vm.edit();
  }

  $scope.$on(events.GROUP_FOCUSED, function() {
    var draftDomainModel;
    var isShared;
    var newGroup;

    if (!vm.editing) {
      return;
    }

    if (!model.id) {
      newGroup = groups.focused().id;
      isShared = permissions.isShared(
        vm.annotation.permissions, vm.annotation.group);
      if (isShared) {
        model.permissions = permissions.shared(newGroup);
        vm.annotation.permissions = model.permissions;
      }
      model.group = newGroup;
      vm.annotation.group = model.group;
    }

    if (drafts.get(model)) {
      draftDomainModel = {};
      updateDomainModel(draftDomainModel, vm.annotation);
      updateDraft(draftDomainModel);
    }
  });

  return vm;
}

// @ngInject
/**
  * @ngdoc directive
  * @name annotation
  * @restrict A
  * @description
  * Directive that instantiates
  * {@link annotation.AnnotationController AnnotationController}.
  *
  */
function annotation($document, features) {
  function linkFn(scope, elem, attrs, controllers) {
    var ctrl = controllers[0];
    var thread = controllers[1];
    var threadFilter = controllers[2];
    var counter = controllers[3];

    attrs.$observe('isSidebar', function(value) {
      if (value) {
        ctrl.isSidebar = true;
      } else {
        ctrl.isSidebar = false;
      }
    });

    elem.on('keydown', function(event) {
      if (event.keyCode === 13 && (event.metaKey || event.ctrlKey)) {
        event.preventDefault();
        scope.$evalAsync(function() {
          ctrl.save();
        });
      }
    });

    scope.feature = features.flagEnabled;

    scope.share = function(event) {
      var $container;
      $container = angular.element(event.currentTarget).parent();
      $container.addClass('open').find('input').focus().select();
      event.stopPropagation();
      $document.one('click', function() {
        $container.removeClass('open');
      });
    };

    if (counter !== null) {
      scope.$watch((function() {
        counter.count('edit');
      }), function(count) {
        if (count && !ctrl.editing && thread.collapsed) {
          thread.toggleCollapsed();
        }
      });

      scope.$watch((function() {return ctrl.editing;}), function(editing, old) {
        if (editing) {
          counter.count('edit', 1);
          if ((thread !== null) && (threadFilter !== null)) {
            threadFilter.active(false);
            threadFilter.freeze(true);
          }
        } else if (old) {
          counter.count('edit', -1);
          threadFilter !== null ? threadFilter.freeze(false) : void 0;
        }
      });

      scope.$on('$destroy', function() {
        if (ctrl.editing) {
          counter !== null ? counter.count('edit', -1) : void 0;
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
      isLastReply: '=',
      replyCount: '@annotationReplyCount',
      replyCountClick: '&annotationReplyCountClick',
      showReplyCount: '@annotationShowReplyCount'
    },
    templateUrl: 'annotation.html'
  };
}

module.exports = {
  validate: validate,
  directive: annotation,
  Controller: AnnotationController
};
