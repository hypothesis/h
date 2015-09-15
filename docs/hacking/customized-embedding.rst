Customized embedding
####################

To customize the application, define a function ``window.hypothesisConfig``
which returns an options object.

The ``constructor`` property should be used to select an annotation
application. Four are provided: ``Annotator.Guest``, ``Annotator.Host``,
``Annotator.Sidebar`` and ``Annotator.PdfSidebar``.

``Annotator.Guest`` expects to connect to an annotator widget running in a
different frame. Any number of instances can communicate with a single widget
in order to provide annotation of many frames.

``Annotator.Host`` is an extended version of ``Annotator.Guest`` that will
instantiate an annotator widget by loading the location given by the ``app``
option in an iframe and appending it to the document.

``Annotator.Sidebar`` is an extended ``Annotator.Host`` that puts the widget
in a sidebar interface. It loads additional plugins that show a bar of bucket
indicators, each providing the ability to select a cluster of highlights, and a
toolbar that can be used to resize the widget and control other aspects of the
user interface.

``Annotator.PdfSidebar`` is a custom version of ``Annotator.Sidebar`` with
defaults tailored for use in a PDF.js viewer.

The following is roughly the default configuration::

    window.hypothesisConfig = function () {
      return {
        constructor: Annotator.Sidebar,
        app: 'https://hypothes.is/app.html'
      };
    };
