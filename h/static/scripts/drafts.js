/**
 * The drafts service provides temporary storage for unsaved edits
 * to new or existing annotations.
 *
 * A draft consists of a 'model' which is the original annotation
 * which the draft is associated with and `changes' which is
 * a set of edits to the original annotation.
 */
function DraftStore() {
  this._drafts = [];

  // returns true if 'draft' is a draft for a given
  // annotation. Annotations are matched by ID
  // and annotation instance (for unsaved annotations
  // which have no ID)
  function match(draft, model) {
    return draft.model === model ||
           (draft.model.id && model.id === draft.model.id);
  }

  /**
   * Returns a list of all new annotations (those with no ID) for which
   * unsaved drafts exist.
   */
  this.unsaved = function unsaved() {
    return this._drafts.filter(function (draft) {
      return !draft.model.id;
    }).map(function (draft) {
      return draft.model;
    });
  }

  /** Retrieve the draft changes for an annotation. */
  this.get = function get(model) {
    for (var i=0; i < this._drafts.length; i++) {
      if (match(this._drafts[i], model)) {
        return this._drafts[i].changes;
      }
    }
  }

  /**
   * Update the draft version for a given annotation, replacing any
   * existing draft.
   */
  this.update = function update(model, changes) {
    var newDraft = {
      model: model,
      changes: changes,
    };
    this.remove(model);
    this._drafts.push(newDraft);
  }

  /** Remove the draft version of an annotation. */
  this.remove = function remove(model) {
    this._drafts = this._drafts.filter(function (draft) {
      return !match(draft, model);
    });
  }

  /** Prompt to discard any unsaved drafts. */
  this.discard = function discard() {
    // TODO - Replace this with a UI which doesn't look terrible
    var text;
    if (this._drafts.length === 1) {
      text = 'You have an unsaved reply.\n\n' +
             'Do you really want to discard this draft?';
    } else if (this._drafts.length > 1) {
      text = 'You have ' + this._drafts.length + ' unsaved replies.\n\n'
             'Do you really want to discard these drafts?';
    }
    if (this._drafts.length === 0 || window.confirm(text)) {
      this._drafts = [];
      return true;
    } else {
      return false;
    }
  }
}

module.exports = function () {
  return new DraftStore();
};
