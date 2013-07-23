/* Load this script using conditional IE comments if you need to support IE 7 and IE 6. */

window.onload = function() {
	function addIcon(el, entity) {
		var html = el.innerHTML;
		el.innerHTML = '<span style="font-family: \'icomoon\'">' + entity + '</span>' + html;
	}
	var icons = {
			'icon-untitled' : '&#x22;',
			'icon-untitled-2' : '&#x23;',
			'icon-untitled-3' : '&#x24;',
			'icon-untitled-4' : '&#x25;',
			'icon-untitled-5' : '&#x26;',
			'icon-untitled-6' : '&#x27;',
			'icon-untitled-7' : '&#x28;',
			'icon-untitled-8' : '&#x29;',
			'icon-untitled-9' : '&#x2b;',
			'icon-untitled-10' : '&#x2c;',
			'icon-untitled-11' : '&#x2f;',
			'icon-untitled-12' : '&#x33;',
			'icon-untitled-13' : '&#x34;',
			'icon-untitled-14' : '&#x36;',
			'icon-untitled-15' : '&#x38;',
			'icon-untitled-16' : '&#x39;',
			'icon-untitled-17' : '&#x3a;',
			'icon-untitled-18' : '&#x35;',
			'icon-untitled-19' : '&#x37;',
			'icon-untitled-20' : '&#x2a;',
			'icon-untitled-21' : '&#x3e;',
			'icon-untitled-22' : '&#x3f;',
			'icon-untitled-23' : '&#x3c;',
			'icon-untitled-24' : '&#xe000;',
			'icon-untitled-25' : '&#xe001;',
			'icon-untitled-26' : '&#xe002;',
			'icon-untitled-27' : '&#xe003;',
			'icon-untitled-28' : '&#xe007;',
			'icon-untitled-29' : '&#xe008;',
			'icon-untitled-30' : '&#xe004;',
			'icon-untitled-31' : '&#xe005;',
			'icon-untitled-32' : '&#xe006;',
			'icon-untitled-33' : '&#xe009;',
			'icon-untitled-34' : '&#xe00a;',
			'icon-untitled-35' : '&#xe00b;',
			'icon-untitled-36' : '&#xe00c;',
			'icon-untitled-37' : '&#xe00e;',
			'icon-untitled-38' : '&#xe00d;',
			'icon-untitled-39' : '&#xe00f;',
			'icon-untitled-40' : '&#xe020;',
			'icon-untitled-41' : '&#xe010;',
			'icon-untitled-42' : '&#xe014;',
			'icon-untitled-43' : '&#xf000;',
			'icon-plus' : '&#xe011;',
			'icon-menu' : '&#xe012;',
			'icon-pen-alt-fill' : '&#xe013;'
		},
		els = document.getElementsByTagName('*'),
		i, attr, html, c, el;
	for (i = 0; ; i += 1) {
		el = els[i];
		if(!el) {
			break;
		}
		attr = el.getAttribute('data-icon');
		if (attr) {
			addIcon(el, attr);
		}
		c = el.className;
		c = c.match(/icon-[^\s'"]+/);
		if (c && icons[c[0]]) {
			addIcon(el, icons[c[0]]);
		}
	}
};