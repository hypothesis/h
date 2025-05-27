/**
 * Return an HTML5 audio player with the given src URL.
 */
function audioElement(src: string): HTMLAudioElement {
  const html5audio = document.createElement('audio');
  html5audio.controls = true;
  html5audio.src = src;
  return html5audio;
}

/**
 * Wrap an element in a container that causes the element to be displayed at
 * a given aspect ratio.
 *
 * See https://css-tricks.com/aspect-ratio-boxes/.
 *
 * @param element
 * @param aspectRatio - Aspect ratio as `width/height`
 * @return - A container element which wraps `element`
 */
function wrapInAspectRatioContainer(
  element: HTMLElement,
  aspectRatio: number,
): HTMLElement {
  element.style.position = 'absolute';
  element.style.top = '0';
  element.style.left = '0';
  element.style.width = '100%';
  element.style.height = '100%';

  const container = document.createElement('div');
  container.style.paddingBottom = `${(1 / aspectRatio) * 100}%`;
  container.style.position = 'relative';
  container.appendChild(element);

  return container;
}

/**
 * Return an iframe DOM element with the given src URL.
 */
function iframe(src: string, aspectRatio = 16 / 9): HTMLElement {
  const iframe_ = document.createElement('iframe');
  iframe_.src = src;
  iframe_.setAttribute('frameborder', '0');
  iframe_.setAttribute('allowfullscreen', '');

  return wrapInAspectRatioContainer(iframe_, aspectRatio);
}

/**
 * Return timeValue as a value in seconds, supporting `t` param's optional
 * '\dh\dm\ds' format. If `timeValue` is numeric (only),
 * it's assumed to be seconds and is left alone.
 *
 * @param timeValue - value of `t` or `start` param in YouTube URL
 * @return timeValue in seconds
 * @example
 * formatYouTubeTime('5m'); // returns '300'
 * formatYouTubeTime('20m10s'); // returns '1210'
 * formatYouTubeTime('1h1s'); // returns '3601'
 * formatYouTubeTime('10'); // returns '10'
 **/
function parseTimeString(timeValue: string): string {
  const timePattern = /(\d+)([hms]?)/g;
  const multipliers = {
    h: 60 * 60,
    m: 60,
    s: 1,
  };
  let seconds = 0;
  let match;
  // match[1] - Numeric value
  // match[2] - Unit (e.g. 'h','m','s', or empty)
  while ((match = timePattern.exec(timeValue)) !== null) {
    if (match[2]) {
      const unit = match[2] as keyof typeof multipliers;
      seconds += Number(match[1]) * multipliers[unit];
    } else {
      seconds += +match[1]; // Treat values missing units as seconds
    }
  }
  return seconds.toString();
}

/**
 * Return a YouTube URL query string containing (only) whitelisted params.
 * See https://developers.google.com/youtube/player_parameters for
 * all parameter possibilities.
 *
 * @return Formatted filtered URL query string, e.g. '?start=90' or
 *   an empty string if the filtered query is empty.
 * @example
 * // returns '?end=10&start=5'
 * youTubeQueryParams(link); // where `link.search` = '?t=5&baz=foo&end=10'
 * // - `t` is translated to `start`
 * // - `baz` is not allowed param
 * // - param keys are sorted
 */
function youTubeQueryParams(link: HTMLAnchorElement): string {
  const allowedParams = [
    'end',
    'start',
    't', // will be translated to `start`
  ];
  const linkParams = new URLSearchParams(link.search);
  const filteredQuery = new URLSearchParams();

  // Copy allowed params into `filteredQuery`.
  for (const [key, value] of linkParams) {
    if (!allowedParams.includes(key)) {
      continue;
    }
    if (key === 't') {
      // `t` is not supported in embeds; `start` is
      // `t` accepts more formats than `start`; start must be in seconds
      // so, format it as seconds first
      filteredQuery.append('start', parseTimeString(value));
    } else {
      filteredQuery.append(key, value);
    }
  }

  // Tests currently expect sorted parameters.
  filteredQuery.sort();

  let query = filteredQuery.toString();
  if (query) {
    query = `?${query}`;
  }
  return query;
}

/**
 * Return a YouTube embed (<iframe>) DOM element for the given video ID.
 */
function youTubeEmbed(id: string, link: HTMLAnchorElement): HTMLElement {
  const query = youTubeQueryParams(link);
  return iframe(`https://www.youtube.com/embed/${id}${query}`);
}

/**
 * Create an iframe embed generator for links that have the form
 * `https://<hostname>/<path containing a video ID>`
 *
 * @param pathPattern -
 *   Pattern to match against the pathname part of the link. This regex should
 *   contain a single capture group which matches the video ID within the path.
 * @param iframeUrlGenerator -
 *   Generate the URL for an embedded video iframe from a video ID
 * @return Function that takes an `<a>` element and returns the embedded iframe
 *   for that link, or `null` if we don't have a matching embed generator.
 */
function createEmbedGenerator(
  hostname: string,
  pathPattern: RegExp,
  iframeUrlGenerator: (videoId: string) => string,
  { aspectRatio }: { aspectRatio?: number } = {},
): (link: HTMLAnchorElement) => HTMLElement | null {
  const generator = (link: HTMLAnchorElement) => {
    if (link.hostname !== hostname) {
      return null;
    }

    const groups = pathPattern.exec(link.pathname);
    if (!groups) {
      return null;
    }

    const id = groups[1];
    return iframe(iframeUrlGenerator(id), aspectRatio);
  };

  return generator;
}

/**
 * A list of functions that return an "embed" DOM element (e.g. an <iframe> or
 * an html5 <audio> element) for a given link.
 *
 * Each function either returns `undefined` if it can't generate an embed for
 * the link, or a DOM element if it can.
 */
const embedGenerators: Array<(link: HTMLAnchorElement) => HTMLElement | null> =
  [
    // Matches URLs like https://www.youtube.com/watch?v=rw6oWkCojpw
    function iframeFromYouTubeWatchURL(link) {
      if (link.hostname !== 'www.youtube.com') {
        return null;
      }

      if (!/\/watch\/?/.test(link.pathname)) {
        return null;
      }

      const groups = /[&?]v=([^&#]+)/.exec(link.search);
      if (groups) {
        return youTubeEmbed(groups[1], link);
      }
      return null;
    },

    // Matches URLs like https://youtu.be/rw6oWkCojpw
    function iframeFromYouTubeShareURL(link) {
      if (link.hostname !== 'youtu.be') {
        return null;
      }

      // extract video ID from URL
      const groups = /^\/([^/]+)\/?$/.exec(link.pathname);
      if (groups) {
        return youTubeEmbed(groups[1], link);
      }
      return null;
    },

    // Matches URLs like https://vimeo.com/149000090
    createEmbedGenerator(
      'vimeo.com',
      /^\/([^/?#]+)\/?$/,
      id => `https://player.vimeo.com/video/${id}`,
    ),

    // Matches URLs like https://vimeo.com/channels/staffpicks/148845534
    createEmbedGenerator(
      'vimeo.com',
      /^\/channels\/[^/]+\/([^/?#]+)\/?$/,
      id => `https://player.vimeo.com/video/${id}`,
    ),

    /**
     * Match Internet Archive URLs
     *
     *  The patterns are:
     *
     *  1. https://archive.org/embed/{slug}?start={startTime}&end={endTime}
     *     (Embed links)
     *
     *  2. https://archive.org/details/{slug}?start={startTime}&end={endTime}
     *     (Video page links for most videos)
     *
     *  3. https://archive.org/details/{slug}/start/{startTime}/end/{endTime}
     *     (Video page links for the TV News Archive [1])
     *
     *  (2) and (3) allow users to copy and paste URLs from archive.org video
     *  details pages directly into the sidebar to generate video embeds.
     *
     *  [1] https://archive.org/details/tv
     */
    function iFrameFromInternetArchiveLink(link: HTMLAnchorElement) {
      if (link.hostname !== 'archive.org') {
        return null;
      }

      // Extract the unique slug from the path.
      const slugMatch = /^\/(embed|details)\/(.+)/.exec(link.pathname);
      if (!slugMatch) {
        return null;
      }

      // Extract start and end times, which may appear either as query string
      // params or path params.
      let slug = slugMatch[2];
      const linkParams = new URLSearchParams(link.search);
      let startTime = linkParams.get('start');
      let endTime = linkParams.get('end');

      if (!startTime) {
        const startPathParam = slug.match(/\/start\/([^/]+)/);
        if (startPathParam) {
          startTime = startPathParam[1];
          slug = slug.replace(startPathParam[0], '');
        }
      }

      if (!endTime) {
        const endPathParam = slug.match(/\/end\/([^/]+)/);
        if (endPathParam) {
          endTime = endPathParam[1];
          slug = slug.replace(endPathParam[0], '');
        }
      }

      // Generate embed URL.
      const iframeUrl = new URL(`https://archive.org/embed/${slug}`);
      if (startTime) {
        iframeUrl.searchParams.append('start', startTime);
      }
      if (endTime) {
        iframeUrl.searchParams.append('end', endTime);
      }
      return iframe(iframeUrl.href);
    },

    // Matches URLs that end with .mp3, .ogg, or .wav (assumed to be audio files)
    function html5audioFromMp3Link(link: HTMLAnchorElement) {
      if (
        link.pathname.endsWith('.mp3') ||
        link.pathname.endsWith('.ogg') ||
        link.pathname.endsWith('.wav')
      ) {
        return audioElement(link.href);
      }
      return null;
    },
  ];

/**
 * Return an embed element for the given link if it's an embeddable link.
 *
 * If the link is a link for a YouTube video or other embeddable media then
 * return an embed DOM element (for example an <iframe>) for that media.
 */
function embedForLink(link: HTMLAnchorElement): HTMLElement | null {
  let embed;
  let j;
  for (j = 0; j < embedGenerators.length; j++) {
    embed = embedGenerators[j](link);
    if (embed) {
      return embed;
    }
  }
  return null;
}

/**
 * Replace the given link element with an embed.
 *
 * If the given link element is a link to an embeddable media and if its link
 * text is the same as its href then it will be replaced in the DOM with an
 * embed (e.g. an <iframe> or html5 <audio> element) of the same media.
 *
 * If the link text is different from the href, then the link will be left
 * untouched. We want to convert links like these from the Markdown source into
 * embeds:
 *
 *     https://vimeo.com/channels/staffpicks/148845534
 *     <https://vimeo.com/channels/staffpicks/148845534>
 *
 * But we don't want to convert links like this:
 *
 *     [Custom link text](https://vimeo.com/channels/staffpicks/148845534)
 *
 * because doing so would destroy the user's custom link text, and leave users
 * with no way to just insert a media link without it being embedded.
 *
 * If the link is not a link to an embeddable media it will be left untouched.
 */
function replaceLinkWithEmbed(link: HTMLAnchorElement): HTMLElement | null {
  // The link's text may or may not be percent encoded. The `link.href` property
  // will always be percent encoded. When comparing the two we need to be
  // agnostic as to which representation is used.
  if (link.href !== link.textContent) {
    try {
      const encodedText = encodeURI(link.textContent!);
      if (link.href !== encodedText) {
        return null;
      }
    } catch {
      return null;
    }
  }

  const embed = embedForLink(link);
  if (embed) {
    link.parentElement!.replaceChild(embed, link);
  }
  return embed;
}

export type EmbedOptions = {
  /**
   * Class name to apply to embed containers. An important function of this
   * class is to set the width of the embed.
   */
  className?: string;
};

/**
 * Replace all embeddable link elements beneath the given element with embeds.
 *
 * All links to YouTube videos or other embeddable media will be replaced with
 * embeds of the same media.
 *
 * @param element - Root element to search for links
 */
export function replaceLinksWithEmbeds(
  element: HTMLElement,
  { className }: EmbedOptions = {},
) {
  // Get a static (non-live) list of <a> children of `element`.
  // It needs to be static because we may replace these elements as we iterate over them.
  const links = Array.from(element.getElementsByTagName('a'));

  for (const link of links) {
    const embed = replaceLinkWithEmbed(link);
    if (embed) {
      if (className) {
        embed.className = className;
      } else {
        // Default width.
        embed.style.width = '350px';
      }
    }
  }
}
