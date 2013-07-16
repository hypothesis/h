# Plugin that will display a notification to the user if thier browser does
# not support the Annotator.
class Annotator.Plugin.Unsupported extends Annotator.Plugin
  # Options Object, message sets the message displayed in the browser.
  options:
    message: Annotator._t("Sorry your current browser does not support the Annotator")

  # Public: Checks the Annotator.supported() method and if unsupported displays
  # @options.message in a notification.
  #
  # Returns nothing.
  pluginInit: ->
    unless Annotator.supported()
      $(=>
        # On document load display notification.
        Annotator.showNotification(@options.message)

        # Add a class if we're in IE6. A bit of a hack but we need to be able
        # to set the notification position in the CSS.
        if (window.XMLHttpRequest == undefined) and (ActiveXObject != undefined)
          $('html').addClass('ie6')
      )
