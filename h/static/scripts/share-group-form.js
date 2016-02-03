function ShareGroupFormController(element) {
  if (!element.querySelector('.is-member-of-group')) {
    return;
  }
  var shareLink = element.querySelector('.js-share-link');
  shareLink.focus();
  shareLink.select();
}

module.exports = ShareGroupFormController;
