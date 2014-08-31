#TinyMCE Latex Plugin

It does what it says: you write LaTeX code, it inserts an image rendered through Google Infographics API in your fav web rich text editor.

[You can try it live here](http://moonwave99.github.com/TinyMCELatexPlugin/).

You can:

* Write new formulae;
* Edit existing ones;
* See preview of the code you are writing.
* It's a very simple thing, Google does all the work - please tell me if you find any bug.

##Installation

* [Get the plugin](https://github.com/moonwave99/TinyMCELatexPlugin/zipball/master);
* Unzip it into the plugins folder of TinyMCE;
* Wherever you startup a TinyMCE editor, register the plugin.

Using the [TinyMCE jQuery Plugin](http://www.tinymce.com/tryit/jquery_plugin.php):

	$('#yourTextArea').tinymce({
	    ...
	    // General options
	    theme : "advanced",
	    plugins : "autolink,lists, ... ,latex",
	    ...
	    // Theme options
	    ...
	    // Put the plugin wherever you want!
	    theme_advanced_buttons2 : "...,latex,|,...",
    
	    ...
    
	});
    
You are done - go write a post about Zeta Function and Megan Fox now.