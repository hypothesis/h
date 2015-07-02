Customized embedding
####################

To customize the plugins that are loaded, define a function ``window.hypothesisConfig``
which returns an options object::


    window.hypothesisConfig = function () {
      return {
        app: 'https://example.com/custom_sidebar_iframe',
        Toolbar: {container: '.toolbar-wrapper'},
        BucketBar: {container: '.bucketbar-wrapper'}
      };
    };

In the above example, the Toolbar will be attached to the element with the
``.toolbar-wrapper`` class, and the BucketBar to the element with the ``.bucketbar-wrapper``
class.

The full range of possibilities here is still in need of documentation and we
would appreciate any help to improve that.

With the exception of ``app`` and ``constructor``, the properties for the options object
are the names of Annotator plugins and their values are the options passed to the individual
plugin constructors.

The ``app`` property should be a url pointing to the HTML document that will be
embedded in the page.

The ``constructor`` property should be used in when you want to annotate an iframe on a host
document. By instantiating the ``Annotator.Guest`` class inside the iframe you can capture
selection data from the frame which will be accessible by a host annotator in a parent document.
By default, Hypothesis instantiates the ``Annotator.Host`` class defined in the injected code
loaded by ``embed.js``. It is possible to change this by assigning an alternate ``constructor``
in the options object returned by ``window.hypothesisConfig``. For example::


	window.hypothesisConfig = function () {
		return {
			constructor: Annotator.Guest
		};
	};

An Annotator Host can connect to multiple guests.
