'use strict';

module.exports = {

  /**
   * compare two list arrays and decide if they have changed
   *
   * @param  {Array} listA
   * @param  {Array} listB
   * @returns {bool}       the result of comparing if the two
   *   arrays seem like they have changed. True if they have changed
   */
  listIsDifferent: function(listA, listB) {

    if (!(Array.isArray(listA) && Array.isArray(listB))) {
      return true;
    }

    if (listA.length !== listB.length) {
      return true;
    }

    return !listA.every((item, index) => {
      return item === listB[index];
    });
  },
};
