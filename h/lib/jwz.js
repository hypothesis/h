// example usage:
// thread = mail.messageThread().thread(messages.map(
//   function(message) {
//     return mail.message(message.subject, message.messageId, message.references);
//   }
// ));
// conversation = thread.getConversation(messageId);

(function() {

  function message(subject, id, references) {
    return function(subject, id, references) {
      return {
        subject: subject,
        id: id,
        references: references
      }
    }(subject, id, references);
  }

  function messageContainer(message) {
    return function(message) {
      var children = [];

      function getConversation(id) {
        var child = this.getSpecificChild(id);
        var flattened = [];
        if(child) flattened = child.flattenChildren();
        if(child.message) flattened.unshift(child.message);
        return flattened;
      }

      function flattenChildren() {
        var messages = [];
        this.children.forEach(function(child) {
          if (child.message) messages.push(child.message);
          var nextChildren = child.flattenChildren();
          if (nextChildren) {
            nextChildren.forEach(function(nextChild) {
              messages.push(nextChild);
            })
          }
        });
        if (messages.length > 0) return messages;
      }

      function getSpecificChild(id) {
        var instance = this;
        if (instance.message && instance.message.id == id) return instance;
        var specificChild = null;
        instance.children.forEach(function(child) {
          var found = child.getSpecificChild(id);
          if (found) {
            specificChild = found;
            return;
          }
        })
        return specificChild;
      }

      function threadParent() {
        if (!this.message) return this;
        var next = this.parent;
        if (!next) return this;
        var top = next;
        while (next) {
          next = next.parent;
          if (next) {
            if (!next.message) return top;
            top = next;
          }
        }
        return top;
      }

      function addChildToPos(child, pos) {
        if(child.parent) child.parent.removeChild(child);
        this.children.splice(pos,0,child);
        child.parent = this;
      }

      function addChild(child) {
        if(child.parent) child.parent.removeChild(child);
        this.children.push(child);
        child.parent = this;
      }

      function removeChild(child) {
        this.children = this.children.filter(function (other) {
          return other !== child
        });
        delete child.parent;
      }

      function hasDescendant(container) {
        if (this === container) return true;
        if (this.children.length < 1) return false;
        var descendantPresent = false;
        this.children.forEach(function(child) {
          if(child.hasDescendant(container)) descendantPresent = true;
        })
        return descendantPresent;
      }

      return {
        message: message,
        children: children,
        flattenChildren: flattenChildren,
        getConversation: getConversation,
        getSpecificChild: getSpecificChild,
        threadParent: threadParent,
        addChild: addChild,
        addChildToPos: addChildToPos,
        removeChild: removeChild,
        hasDescendant: hasDescendant
      }
    }(message);
  }

  function messageThread() {
    return function() {
      var idTable = {};

      function thread(messages) {
        idTable = this.createIdTable(messages);
        var root = messageContainer();
        Object.keys(idTable).forEach(function(id) {
          var container = idTable[id];
          if (typeof(container.parent) === 'undefined') {
            root.addChild(container);
          }
        })
        pruneEmpties(root);
        return root;
      }

      function pruneEmpties(parent) {
        for(var i = parent.children.length - 1; i >= 0; i--) {
          var container = parent.children[i];
          pruneEmpties(container);
          if (!container.message && container.children.length === 0) {
            parent.removeChild(container);
          } else if (!container.message && container.children.length > 0) {
            if (!parent.parent && container.children.length === 1) {
              promoteChildren(parent, container)
            } else if (!parent.parent && container.children.length > 1) {
              // do nothing
            } else {
              promoteChildren(parent, container)
            }
          }
        }
      }

      function promoteChildren(parent, container) {
        for(var i = container.children.length - 1; i >= 0; i--) {
          var child = container.children[i];
          parent.addChild(child);
        }
        parent.removeChild(container);
      }

      function createIdTable(messages) {
        idTable = {};
        messages.forEach(function(message) {
          var parentContainer = getContainer(message.id);
          parentContainer.message = message;
          var prev = null;
          var references = message.references || [];
          if (typeof(references) == 'string') {
            references = [references]
          }
          references.forEach(function(reference) {
            var container = getContainer(reference);
            if (prev && typeof(container.parent) === 'undefined'
                && !container.hasDescendant(prev)) {
              prev.addChild(container);
            }
            prev = container;
          })
          if (prev && !parentContainer.hasDescendant(prev)) {
            prev.addChild(parentContainer);
          }
        })
        return idTable;
      }

      function getContainer(id) {
        if (typeof(idTable[id]) !== 'undefined') {
          return idTable[id];
        } else {
          return createContainer(id);
        }
      }

      function createContainer(id) {
        var container = mail.messageContainer();
        idTable[id] = container;
        return container;
      }

      function groupBySubject(root) {
        var subjectTable = {};
        root.children.forEach(function(container) {
          if(!container.message) {
            var c = container.children[0];
          } else {
            var c = container;
          }
          if (c && c.message) {
            var message = c.message;
          } else {
            return;
          }
          var subject = helpers.normalizeSubject(message.subject);
          if (subject.length === 0) return;
          var existing = subjectTable[subject];

          if (!existing) {
            subjectTable[subject] = c;
          } else if (
            (typeof(existing.message) !== "undefined") && (
              (typeof(c.message) === "undefined") ||
              (helpers.isReplyOrForward(existing.message.subject)) &&
              (!helpers.isReplyOrForward(message.subject))
            )
          ) {
            subjectTable[subject] = c;
          }
        })

        for(var i = root.children.length - 1; i >= 0; i--) {
          var container = root.children[i];

          if (container.message) {
            var subject = container.message.subject;
          } else {
            var subject = container.children[0].message.subject;
          }

          subject = helpers.normalizeSubject(subject);
          var c = subjectTable[subject];

          if (!c || c === container) continue;

          if (
            (typeof(c.message) === "undefined") &&
            (typeof(container.message) === "undefined")
          ) {
            container.children.forEach(function(ctr) {
              c.addChild(ctr);
            })
            container.parent.removeChild(container);
          } else if (
            (typeof(c.message) === "undefined") &&
            (typeof(container.message) !== "undefined")
          ) {
            c.addChild(container);
          } else if (
            (!helpers.isReplyOrForward(c.message.subject)) &&
            (helpers.isReplyOrForward(container.message.subject))
          ) {
            c.addChild(container);
          } else {
            var newContainer = mail.messageContainer();
            newContainer.addChild(c);
            newContainer.addChild(container);
            subjectTable[subject] = newContainer;
          }
        }

        return subjectTable;
      }

      return {
        getContainer: getContainer,
        createContainer: createContainer,
        createIdTable: createIdTable,
        promoteChildren: promoteChildren,
        pruneEmpties: pruneEmpties,
        groupBySubject: groupBySubject,
        thread: thread,
        get idTable() { return idTable; }
      }
    }();
  }

  var helpers = {
    isReplyOrForward: function(subject) {
      var pattern = /^(Re|Fwd)/i;
      var match = subject.match(pattern);
      return match ? true : false;
    },

    normalizeSubject: function(subject) {
      var pattern = /((Re|Fwd)(\[[\d+]\])?:(\s)?)*([\w]*)/i;
      var match = subject.match(pattern);
      return match ? match[5] : false;
    },

    normalizeMessageId: function(messageId) {
      var pattern = /<([^<>]+)>/;
      var match = messageId.match(pattern);
      return match ? match[1] : null;
    },

    parseReferences: function(references) {
      if (!references) return null;
      var pattern = /<[^<>]+>/g;
      return references.match(pattern).map(function(match) {
        return match.match(/[^<>]+/)[0];
      })
    }
  }

  var mail = this.mail = {
    message: message,
    messageContainer: messageContainer,
    messageThread: messageThread,
    helpers: helpers
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = mail;
  }

})();
