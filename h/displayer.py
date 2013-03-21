import json
import urllib2
import BeautifulSoup
from urlparse import urlparse
 
import time
from dateutil.parser import parse
from datetime import datetime
from dateutil.tz import tzutc
from math import floor

import logging
log = logging.getLogger(__name__)


class DisplayerTemplate(object):
    def __init__(self, annotation):
        self._annotation = annotation
       
    def _url_values(self):
        #Getting the title of the uri.
        #hdrs magic is needed because urllib2 is forbidden to use with default settings.
        hdrs = { 'User-Agent': "Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11" } 
        req = urllib2.Request(self._annotation['uri'], headers = hdrs)
        soup = BeautifulSoup.BeautifulSoup(urllib2.urlopen(req))
        title = soup.title.string if soup.title else self._annotation['uri']
        
        #Favicon
        favlink = soup.find("link", rel="shortcut icon")
        log.info(str(favlink))
        icon_link = favlink['href'] if favlink and favlink['href'] else ''
        log.info(str(icon_link))
        
        #Getting the domain from the uri, and the same url magic for the domain title
        parsed_uri = urlparse(self._annotation['uri'])
        domain = '{}://{}/'.format( parsed_uri[ 0 ], parsed_uri[ 1 ] )
        req2 = urllib2.Request(domain, headers = hdrs)
        soup2 = BeautifulSoup.BeautifulSoup(urllib2.urlopen(req2))
        domain_title = soup2.title.string if soup2.title else domain
        
        return {
            'title'         : title,
            'domain'        : domain,
            'domain_title'  : domain_title,
            'favicon_link'  : icon_link            
        }

    def _fuzzyTime(self, date):        
        if not date: return ''
        log.info(date)
        converted = parse(date)
        log.info(converted)
        log.info(str(datetime.utcnow().replace(tzinfo=tzutc())))
                 
        delta = round((datetime.utcnow().replace(tzinfo=tzutc()) - converted).total_seconds())
        #delta = round((converted - datetime(1970, 1, 1, tzinfo=tzutc())).total_seconds())
        #delta = round((time.time - converted) / 1000)
        log.info(delta)

        minute = 60
        hour = minute * 60
        day = hour * 24
        week = day * 7
        month = day * 30

        if (delta < 30): fuzzy = 'moments ago'
        elif (delta < minute): fuzzy = str(delta) + ' seconds ago'
        elif (delta < 2 * minute): fuzzy = 'a minute ago'
        elif (delta < hour): fuzzy = str(floor(delta / minute)) + ' minutes ago'
        elif (floor(delta / hour) == 1): fuzzy = '1 hour ago'
        elif (delta < day): fuzzy = str(floor(delta / hour)) + ' hours ago'
        elif (delta < day * 2): fuzzy = 'yesterday'
        elif (delta < month): fuzzy = str(round(delta / day)) + ' days ago'
        else: fuzzy = str(converted)
        
        log.info(fuzzy)
        return fuzzy
         
    def _userName(self, user):
        log.info(user)
        if not user: return ''
        if user == '': return 'Annotation deleted.'
        else:
            return user.split(':')[1].split('@')[0]
         
    def generate_dict(self):
        d = {'annotation'    : self._annotation}
        d.update(self._url_values())
        d['fuzzy_date'] = self._fuzzyTime(self._annotation['updated'])
        d['readable_user'] = self._userName(self._annotation['user'])
        return d
