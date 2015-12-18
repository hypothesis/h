'use strict';

/**
 * Return an iframe DOM element with the given src URL.
 */
function iframe(src) {
  var iframe_ = document.createElement('iframe');
  iframe_.src = src;
  iframe_.classList.add('annotation-media-embed');
  iframe_.setAttribute('frameborder', '0');
  iframe_.setAttribute('allowfullscreen', '');
  return iframe_;
}

/**
 * Return a YouTube embed (<iframe>) DOM element for the given video ID.
 */
function youTubeEmbed(id) {
  return iframe('https://www.youtube.com/embed/' + id);
}

function vimeoEmbed(id) {
  return iframe('https://player.vimeo.com/video/' + id);
}

/**
 * A list of functions that return an "embed" DOM element (e.g. an <iframe>)
 * for a given link.
 *
 * Each function either returns `undefined` if it can't generate an embed for
 * the link, or a DOM element if it can.
 *
 */
var embedGenerators = [

  // Matches URLs like https://www.youtube.com/watch?v=rw6oWkCojpw
  function iframeFromYouTubeWatchURL(link) {
    if (link.hostname !== 'www.youtube.com') {
      return;
    }

    if (!/\/watch\/?/.test(link.pathname)) {
      return;
    }

    var groups = /[&\?]v=([^&#]+)/.exec(link.search);
    if (groups) {
      return youTubeEmbed(groups[1]);
    }
  },

  // Matches URLs like https://youtu.be/rw6oWkCojpw
  function iframeFromYouTubeShareURL(link) {
    if (link.hostname !== 'youtu.be') {
      return;
    }

    var groups = /^\/([^\/]+)\/?$/.exec(link.pathname);
    if (groups) {
      return youTubeEmbed(groups[1]);
    }
  },

  // Matches URLs like https://vimeo.com/149000090
  function iFrameFromVimeoLink(link) {
    if (link.hostname !== 'vimeo.com') {
      return;
    }

    var groups = /^\/([^\/\?#]+)\/?$/.exec(link.pathname);
    if (groups) {
      return vimeoEmbed(groups[1]);
    }
  },

  // Matches URLs like https://vimeo.com/channels/staffpicks/148845534
  function iFrameFromVimeoChannelLink(link) {
    if (link.hostname !== 'vimeo.com') {
      return;
    }

    var groups = /^\/channels\/[^\/]+\/([^\/?#]+)\/?$/.exec(link.pathname);
    if (groups) {
      return vimeoEmbed(groups[1]);
    }
  },
];

/**
 * Return an embed element for the given link if it's an embeddable link.
 *
 * If the link is a link for a YouTube video or other embeddable media then
 * return an embed DOM element (for example an <iframe>) for that media.
 *
 * Otherwise return undefined.
 *
 */
function embedForLink(link) {
  var embed;
  var j;
  for (j = 0; j < embedGenerators.length; j++) {
    embed = embedGenerators[j](link);
    if (embed) {
      return embed;
    }
  }
}

/** Replace the given link element with an embed.
 *
 * If the given link element is a link to an embeddable media then it will be
 * replaced in the DOM with an embed (e.g. an <iframe>) of the same media.
 *
 * If it's not an embeddable link the link will be left untouched.
 *
 */
function replaceLinkWithEmbed(link) {

  // If the user gives a custom link text then we don't replace the link with
  // an embed.
  if (link.href !== link.innerText) {
    return;
  }

  var embed = embedForLink(link);
  if (embed) {
    link.parentElement.replaceChild(embed, link);
  }
}


/**
 * Replace all embeddable link elements beneath the given element with embeds.
 *
 * All links to YouTube videos or other embeddable media will be replaced with
 * embeds of the same media.
 *
 */
function replaceLinksWithEmbeds(element) {
  var links = element.getElementsByTagName('a');

  // `links` is a "live list" of the <a> element children of `element`.
  // We want to iterate over `links` and replace some of them with embeds,
  // but we can't modify `links` while looping over it so we need to copy it to
  // a nice, normal array first.
  links = Array.prototype.slice.call(links, 0);

  var i;
  for (i = 0; i < links.length; i++) {
    replaceLinkWithEmbed(links[i]);
  }
}

module.exports = {
  replaceLinksWithEmbeds: replaceLinksWithEmbeds,
};
