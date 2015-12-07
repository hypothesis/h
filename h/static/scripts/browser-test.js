// TODO - Make this a CommonJS module and move it into
// the site JS?
if (window.chrome !== undefined) {
  var elements = document.getElementsByClassName(
      "unhide-in-chrome");
  for (var i=0; i<elements.length; i++) {
    elements[i].classList.remove("hidden");
  }
  elements = document.getElementsByClassName(
      "hide-in-chrome");
  for (var i=0; i<elements.length; i++) {
    elements[i].classList.add("hidden");
  }
}
