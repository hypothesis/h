How to add Hypothesis to your website
#####################################

.. If you update this page, please ensure you update the "For Publishers" page
   on the Hypothesis website, or coordinate with someone who can
   (https://hypothes.is/for-publishers/).

To add Hypothesis to your website, add the following line to the HTML source of
your page:

.. code-block:: html

   <script src="https://hypothes.is/embed.js" async></script>

You can configure Hypothesis by including a config tag above the the script tag.
For example, the following arrangement will ensure that our yellow highlights
are hidden by default:

.. code-block:: html

   <script type="application/json" class="js-hypothesis-config">
   {"showHighlights": false}
   </script>
   <script src="https://hypothes.is/embed.js" async></script>

You can find the `full list of configuration options
<https://github.com/hypothesis/client/blob/master/docs/config.md>`_ in our
client documentation.
