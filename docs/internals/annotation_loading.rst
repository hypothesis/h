Loading and displaying of annotations
================================================


The purpose of this page is to document the process that happens when annotations are loaded and displayed.

* **In sidebar:** on page loading, the annotator store plugin is added. (Annotator: store.coffee)
* When the plugin is activated, the ``_getAnnotations()`` method is called.
* ``loadAnnotationsFromSearch()`` is called, with options defined at plugin init. (URL, etc.)
* When data arrives from the backend, ``_onLoadAnnotationsFromSearch()`` is called, which in turn calls ``_onLoadAnnotations()`` with the data
* ``_onLoadAnnotations()`` stores the data in the (store plugin's) _data_ field, and calls Annotator's ``loadAnnotatations()`` with the data. (Annotator: annotator.coffee)
* ``loadAnnotations()`` breaks the loading process into bunches of 10, and calls ``setupAnnotation()`` method for the loaded annotations, which is overridden by the Hypothesis class. (h: services.coffee).
* ``setupAnnotation()`` adds an empty ranges field for replies (non-reply annotations will already have a range), and (if this is not a reply) using the XDM mechanism, calls Annotator.Host's setupAnnotation, with the ID and ranges of the annotation. (The rest of the annotation's data is not passed.) (h: host.coffee)
* **In host frame:** Annotator.Host's ``setupAnnotation()`` method is called
* It calls the ``setupAnnotation()`` method of it's parent, Annotator (Annotator: annotator.coffee)
* Annotator's ``setupAnnotation()`` method
    * Normalizes the ranges (which is magic, use the Source (in Range.coffee) to understand it)
        * If this step fails (for example, the document has changed, so the specified range can not be found), a **rangeNormalizeFail** event is published. (Nobody seems to be listening to this.)
    * Overwrites the stored ranges with the normalized ones
    * Reads the quotes from the current document (we will ignore those quotes collected here, this is the host frame, only used for highlights and heatmap)
    * Adds highlights for all the ranges
* Back in Annotator.Host's ``setupAnnotation()`` method, some jQuery configuration is done, so that the defined highlighs of the annotations will never be tried to be serialized. (This would normally happen when communicating via XDM, but it won't work here, since those structures contain references to DOM elements.)
* **Back at the sidebar:** When all the annotations have been processed this way, Annotator's ``loadAnnotation()`` method publishes and **annotationsLoaded** event.
* The Hypothesis object (h: services.coffee) has a handler subscribed to the **annotationsLoaded** event, and when it recieves one, it calls the jwz threading library, to build a tree of all the loaded annotations.
* The Hypothes object has an other handler registered for the same event, which 
    * calls Annotator.Host's ``getHighlights()`` method (via XDM)), and with the retrieved data,
    * calls Annotator.Plugin.Heatmap's ``updateHeatmap()`` method.
* **In host frame:** Annotator.Host's ``getHighlights()`` method is invoked. It uses jQuery to collect info about the elements with **annotator-hl** class (those classes were added earlier by Annotator's ``setupAnnotation()`` method, and their positions.
* **Back in sidebar:**  Hypothesis object's event handler has now retreived the highlights. For each of them, it attaches the actual annotation data (stored in by jwz library, accessed from Hypothesis as $threading), and then it calls Annotator.Plugin.Heatmap's ``updateHeatmap()`` method. (h: heatmap.coffee)
* The ``updateHeatmap()`` method updates the heatmap with the received data, and published an **updated** event when ready.
* The summery mode instance of the Viewer (h: controllers.coffee) is subscribed to heatmap's *update* event, with the ``refresh()`` method, so this is called now.
* ``refresh()`` calls ``$scope.focus()``
* ``$scope.focus`` calls Host.Annotator's ``setActiveHighlights()`` method, with an array containing the IDs of all the annotations.
* **In host frame:**: all elements with tha **annotator-hl** class are collected, and the **annotator-hl-active** class is added/removed based on whether the given annotation's id was in the passed ID list.
* App (h: controllers.coffee) is subscribed to heatmap's **update** event, too, and upon receiving it, it does some more magic.


