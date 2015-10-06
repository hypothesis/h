function ShareGroupFormController(element) {
  var shareLink = element.querySelector('.js-share-link');
  shareLink.focus();
  shareLink.select();
}

module.exports = ShareGroupFormController;
