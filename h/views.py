__all__ = [
    'BaseController',

    'AuthController',
    'ForgotPasswordController',
    'RegisterController',
]
from pyramid.traversal import find_resource

import json
import urllib2
import BeautifulSoup
from urlparse import urlparse

import logging
log = logging.getLogger('view')
#TODO: Access annotation class normally
from annotator.annotation import Annotation

from horus.views import (
    AuthController,
    BaseController,
    ForgotPasswordController,
    RegisterController
)


@view_config(layout='site', renderer='templates/home.pt', route_name='index')
def home(request):
    return find_resource(request.context, '/app').embed

@view_config(route_name='displayer',
             renderer='h:templates/displayer.pt',
             layout='lay_displayer')
def displayer(request):
    uid = request.matchdict['uid']
    annotation = Annotation.fetch(uid)
    if not annotation : 
        raise httpexceptions.HTTPNotFound()

    if 'Content-Type' in request.headers and request.headers['Content-Type'].lower() == 'application/json' :
        res = json.dumps(annotation, indent=None if request.is_xhr else 2)
        return Response(res, content_type = 'application/json')
    else :
        #Getting the title of the uri.
        #hdrs magic is needed because urllib2 is forbidden to use with default settings.
        hdrs = { 'User-Agent': "Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11" } 
        req = urllib2.Request(annotation['uri'], headers = hdrs)
        soup = BeautifulSoup.BeautifulSoup(urllib2.urlopen(req))
        title = soup.title.string if soup.title else annotation['uri']
        
        #Favicon
        favlink = soup.find("link", rel="shortcut icon")
        log.info(str(favlink))
        icon_link = favlink['href'] if favlink and favlink['href'] else ''
        log.info(str(icon_link))
        
        #Getting the domain from the uri, and the same url magic for the domain title
        parsed_uri = urlparse(annotation['uri'])
        domain = '{}://{}/'.format( parsed_uri[ 0 ], parsed_uri[ 1 ] )
        req2 = urllib2.Request(domain, headers = hdrs)
        soup2 = BeautifulSoup.BeautifulSoup(urllib2.urlopen(req2))
        domain_title = soup2.title.string if soup2.title else domain
        
        #log.info('Debug')
        #for key, val in annotation.items() :
        #    log.info(str(key) +  ' : ' + str(val))
            
        #Packing the data for the template
        return {
            'quote'         : annotation['quote'],
            'text'          : annotation['text'],
            'user'          : annotation['user'],
            'updated'       : annotation['updated'],
            'uri'           : annotation['uri'],
            'title'         : title,
            'domain'        : domain,
            'domain_title'  : domain_title,
            'favicon_link'  : icon_link
        }



def includeme(config):
    config.add_view(
        'horus.views.AuthController',
        attr='login',
        renderer='h:templates/auth.pt',
        route_name='login'
    )

    config.add_view(
        'horus.views.AuthController',
        attr='logout',
        route_name='logout'
    )

    config.add_view(
        'horus.views.ForgotPasswordController',
        attr='forgot_password',
        renderer='h:templates/auth.pt',
        route_name='forgot_password'
    )

    config.add_view(
        'horus.views.ForgotPasswordController',
        attr='reset_password',
        renderer='h:templates/auth.pt',
        route_name='reset_password'
    )

    config.add_view(
        'horus.views.RegisterController',
        attr='register',
        renderer='h:templates/auth.pt',
        route_name='register'
    )

    config.add_view(
        'horus.views.RegisterController',
        attr='activate',
        renderer='h:templates/auth.pt',
        route_name='activate'
    )

    config.add_view(
        'horus.views.ProfileController',
        attr='profile',
        renderer='h:templates/auth.pt',
        route_name='profile'
    )

    config.scan(__name__)
