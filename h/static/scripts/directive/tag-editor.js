'use strict';

// @ngInject
function TagEditorController(tags) {
  this.onTagsChanged = function () {
    tags.store(this.tagList);

    var newTags = this.tagList.map(function (item) { return item.text; });
    this.onEditTags({tags: newTags});
  };

  this.autocomplete = function (query) {
    return Promise.resolve(tags.filter(query));
  };

  this.$onChanges = function (changes) {
    if (changes.tags) {
      this.tagList = changes.tags.currentValue.map(function (tag) {
        return {text: tag};
      });
    }
  };
}

module.exports = function () {
  return {
    bindToController: true,
    controller: TagEditorController,
    controllerAs: 'vm',
    restrict: 'E',
    scope: {
      tags: '<',
      onEditTags: '&',
    },
    template: require('../../../templates/client/tag_editor.html'),
  };
};
