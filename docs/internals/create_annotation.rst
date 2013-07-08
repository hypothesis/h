Creating a new annotation
==========================================
 
The purpose of this page is to document the process that happens when a new annotation is created.
 
* **In host frame:**  the user begins selecting text, the *mousedown* event is fired and the ``checkForStartSelection()`` method is called. This sets the mouseisDown property to false. (h: host.coffee)
* The selection can begin if the selected text is not part of the annotator (``isAnnotator()`` method), of course in the host.frame nothing should be part of it. (Annotator: annotator.coffee) 
* When the selection ends the *mouseup* event fires and the ``checkForEndSelection()`` method is called and collects the currently selected ranges by calling the ``getSelectedRanges()`` method. (Annotator: annotator.coffee) 
* The user begins creating the annotation by clicking on the *Adder icon* and the ``onAdderClick()`` method is fired.  This method will begin creating the annotation. (Annotator: annotator.coffee)  
	* It calls the ``createAnnotation()`` method  which creates an empty annotation object, publishes the *beforeAnnotationCreated* message and returns the annotation. Here nobody catches that message. (Annotator: annotator.coffee) 
	* The ``onAdderClick()`` calls for the ``setupAnnotation()`` method which is overwritten in the host, but calls the original, and sets the *highlights* property of the annotation to non-serializable. It is needed for the transferring of an annotation between the two frames, which will happen later. (h: host.coffee)
	* The ``setupAnnotation()`` method is called in the annotator. This fills the *ranges* property of the newly created annotation with the selection converted to a range.  After that it makes a range normalization and fills the *quote* and the *highlights* properties of the annotation. (Annotator: annotator.coffee) 
		* The ``highlightRange()`` method is called which wraps the selected range with a highlighter cssClass. (By default: 'annotator-hl')  (Annotator: annotator.coffee)
	* The Annotator.Host subscribes to the *annotatorEditorHidden* and *annotatorEditorSubmit* editor events. (Annotator: annotator.coffee) 
	* Finally the ``onAdderClick()`` calls the ``showEditor()`` method. For a new annotation this methods calls out for the siderbar. (Annotator: annotator.coffee) 
* **In sidebar:**  Via XDM the local ``createAnnotation()`` method of the Hypothesis class is called. This checks for the presence of the *HypothesisPermissions* plugin (and only continues if it's there) and calls the real ``createAnnotation()`` method in this class and finally returns the created *annotation.id* (h: services.coffee)
* The ``createAnnotation()`` method in the Hypothesis class does the following:
	* Calls for the ``createAnnotation()`` method in the Annotator and publishes the *beforeAnnotationCreated* message. (h: services.coffee, Annotator: annotator.coffee)
	* The messaage is catched in the Hypothesis class which adds the *user* property to the annotation (as the current user's userId) and also it defines the 'draft' property for the annotation (h: services.coffee) 
	* The Annotator's ``createAnnotation()`` returns an annotation (with some filled properties) and after that it defines the *annotation.id* property and assign a temporal value to it. Finally this id is returned. (h: services.coffee)
* **back to the host frame:** It assigns the returned temporal annotation.id to the created annotation in this side and after that it calls the other frame again to show the editor. (h: host.coffee)
* **back to the sidebar:**  Via XDM the Hypothesis' class local ``showEditor()`` method is called which checks for the jwz (referenced as threading) whether we store this annotation there. If yes it fetches the all the other data and sets the *thread.message.annotation* with the annotation data. Otherwise it manually assembles it together with the *thread.message.id* and *thread.message.references* data. (The editor will use these.) (h: services.coffee)
* The real ``showEditor()`` method of the Hypothesis class is called which sets the sidebar's url to *'/editor'* and the id to the temporal id. Because of the url change, events will be fired. (h: services.coffee)
* In the Annotation class the *routeChangeStart* message is captured but it does nothing in this scenario. (h: controllers.coffee)
* Because of the URL change, the Viewer is no longer shown and the ``on '$destroy'`` event is fired on it. (h: controllers.coffee)
* Because the 'draft' property was added to the annotation, the Annotation class sets its *$scope.editing* and *unsaved* properties to the value: 'true'. (h: controllers.coffee)
* Because the *editing* property was change the ``$scope.$watch 'editing'`` event is fired and the editor's textarea receives the focus. (h: controllers.coffee)
* The ``show()`` method is called on the sidebar (even if it is already being shown). (h: services.coffee)
	* **back to the host frame:**  During the ``show()`` method the ``showFrame()`` method is called on the Annotator.Host class (h: host.coffee)
* In this point the annotation editor is shown and the user can type it's text.

* After the user clicks the *Save* button the process continues:
* **back to the sidebar:**  The ``$scope.save`` method of the Annotation class is called by clicking the Save button. This sets the *$scope.editing* to false and removes the *draft* property from the annotation. Finally it publishes the *annotationCreated* message (h : controllers.coffee)
* Because the *editing* property was change the ``$scope.$watch 'editing'`` event is fired and the editor's textarea receives the focus. (h: controllers.coffee)
* Because of the fired eventy the ``annotationCreated()`` method gets invoked in the Annotation.Store plugin. (Annotator: store.coffee)
	* This calls the ``registerAnnotations()`` method which  pushes the annotation to the known annotation store. (Annotator: store.coffee)
	* The annotation will be stored in the backend too, for to prepare it the ``annotationCreated()`` calls for the ``_apiRequest()`` method (Annotator: store.coffee)
		* This method assembles the save request with the help of calling the ``_urlFor()`` and the ``_apiRequestOptions()`` methods. (Annotator: store.coffee)
* The Editor class' ``save()``method also reacts for the *annotationCreated* message and it sets the url back to */viewer* and calls the ``onEditorSubmit()``and ``onEditorHide()`` methods of the Annotator.Host (h: controllers.coffee)
		
* Because of the url change the *routeChangeStart* message is captured and the ``$scope.cancel()`` method is invoked which cleans up after the editor. (h: controllers.coffee)
* The Editor's ``$on '$destroy'()`` method is invoked destroying all subscriptions which the Editor had (h: controllers.coffee) 		
* The Viewer's ``refresh()`` method is called. Actually two methods: one in the constructor and one after listening.  These updates the $scope variables to their correct value and because a new Annotation was created it sets the detail mode to true. (h: controllers.coffee)
* The Viewer's ``focus()`` method is called which collects the corresponding highlights and calls the Annotator.Host's ``setActiveHighlights()`` method to set the highlights. (h: controllers.coffee)

* Now the editor is shown with the new annotation, however with some temporary data. This annotation will be updated when the server answer's for the save.
* Hypothesis' Annotator.Store plugin's overwritten ``updateAnnotation()`` method is called as a callback when the save request returns. This method overwrites and updates the annotation from the data fetched from the server. (i.e. getting permanent Id)  It also removes the old annotation data from the threading and creates a new one with the current data.(h: services.coffee)
* **Back to the host frame:** the old annotation data should also be deleted from this side. The ``local.deleteAnnotation()`` method is invoked via XDM (h: host.coffee)
* That calls the ``deleteAnnotation()`` method in the Annotator which removes it's highlight from the DOM and publishes the *annotationDeleted* message (Annotator: annotator.coffee)
* The ``local.loadAnnotations()`` method is invoked via XDM (h: host.coffee)
* That calls the ``loadAnnotations()`` method in the Annotator which loads the new annotation into the Annotator and publishes the *annotationsLoaded* message (Annotator: annotator.coffee)
* Because of that message the ``setupAnnotation()`` method is called again which generates the quote, ranges and highlights properties and sets the highlight. (Annotator: annotator.coffee)

* After that the viewer is refreshed again **in the sidebar** as above and the annotation is finally created.


