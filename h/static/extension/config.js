function hypothesisConfig() {
  // Pages on our site can include a meta tag to trigger specific behaviour
  // when the extension loads.
  var hypothesisIntent = document.querySelector('[name="hypothesis-intent"]');
  return {
    firstRun: hypothesisIntent && hypothesisIntent.content === 'first-run',
  };
}
