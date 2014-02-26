import traceback
import re
from urlparse import urlparse

from horus.models import get_session

from pyramid_mailer.interfaces import IMailer
from pyramid_mailer.message import Message

from pyramid.renderers import render

from pyramid.events import subscriber
from h import events, models
from h.interfaces import IStoreClass
from h.streamer import FilterHandler, parent_values

import logging
log = logging.getLogger(__name__)


def user_profile_url(request, user):
    username = re.search("^acct:([^@]+)", user).group(1)
    return request.application_url + '/u/' + username


def standalone_url(request, id):
    return request.application_url + '/a/' + id


class ReplyTemplate(object):
    template = 'h:templates/emails/reply_notification.txt'

    @staticmethod
    def _create_template_map(request, reply):
        parent_user = re.search("^acct:([^@]+)", reply['parent']['user']).group(1)
        reply_user = re.search("^acct:([^@]+)", reply['user']).group(1)
        parent_tags = '\ntags: ' + ', '.join(reply['parent']['tags']) if 'tags' in reply['parent'] else ''
        reply_tags = '\ntags: ' + ', '.join(reply['tags']) if 'tags' in reply else ''

        return {
            'document_title': reply['title'],
            'document_path': reply['parent']['uri'],
            'parent_quote': reply['parent']['quote'],
            'parent_text': reply['parent']['text'],
            'parent_user': parent_user,
            'parent_tags': parent_tags,
            'parent_timestamp': reply['parent']['created'],
            'parent_user_profile': user_profile_url(request, reply['parent']['user']),
            'parent_path': standalone_url(request, reply['parent']['id']),
            'reply_quote': reply['quote'],
            'reply_text': reply['text'],
            'reply_user': reply_user,
            'reply_tags': reply_tags,
            'reply_timestamp': reply['created'],
            'reply_user_profile': user_profile_url(request, reply['user']),
            'reply_path': standalone_url(request, reply['id'])
        }

    @staticmethod
    def render(request, reply):
        return render(ReplyTemplate.template, ReplyTemplate._create_template_map(request, reply), request)

    @staticmethod
    def generate_notification(request, annotation, data):
        # Get the e-mail of the owner
        if not annotation['parent']['user']: return {'status': False}
        # Do not notify me about my own message
        if annotation['user'] == annotation['parent']['user']: return {'status': False}

        username = re.search("^acct:([^@]+)", annotation['parent']['user']).group(1)
        userobj = models.User.get_by_username(request, username)
        if not userobj:
            log.warn("Warning! User not found! " + str(username))
            return {'status': False}
        recipients = [userobj.email]
        rendered = ReplyTemplate.render(request, annotation)
        subject = "A reply to you at: " + annotation['title'] + \
                  "(" + annotation['uri'] + ")"
        return {
            'status': True,
            'recipients': recipients,
            'rendered': rendered,
            'subject': subject
        }


class CustomSearchTemplate(object):
    template = 'h:templates/emails/custom_search.txt'

    @staticmethod
    def _create_template_map(request, annotation):
        tags = ', '.join(annotation['tags']) if 'tags' in annotation else '(none)'
        return {
            'document_title': annotation['title'],
            'document_path': annotation['uri'],
            'text': annotation['text'],
            'tags': tags,
            'user_profile': user_profile_url(request, annotation['user']),
            'path': standalone_url(request, annotation['id'])
        }

    @staticmethod
    def render(request, annotation):
        return render(CustomSearchTemplate.template,
                      CustomSearchTemplate._create_template_map(request, annotation),
                      request)

    @staticmethod
    def generate_notification(request, annotation, data):
        username = re.search("^acct:([^@]+)", annotation['user']).group(1)
        userobj = models.User.get_by_username(request, username)
        if not userobj:
            log.warn("User not found! " + str(username))
            return {'status': False}
        recipients = [userobj.email]
        rendered = CustomSearchTemplate.render(request, annotation)
        subject = "New annotation for your query: " + annotation['title'] + \
                  "(" + annotation['uri'] + ")"
        return {
            'status': True,
            'recipients': recipients,
            'rendered': rendered,
            'subject': subject
        }


class AnnotationNotifier(object):
    registered_templates = {}

    def __init__(self, request):
        self.request = request
        self.registry = request.registry
        self.mailer = self.registry.queryUtility(IMailer)
        self.store = self.registry.queryUtility(IStoreClass)(request)

    @classmethod
    def register_template(cls, template, function):
        cls.registered_templates[template] = function

    def send_notification_to_owner(self, annotation, data, template):
        if template in self.registered_templates:
            notification = self.registered_templates[template](self.request, annotation, data)
            if notification['status']:
                self._send_annotation(notification['rendered'], notification['subject'], notification['recipients'])

    def _send_annotation(self, body, subject, recipients):
        message = Message(subject=subject,
                          sender="noreply@hypothes.is",
                          recipients=recipients,
                          body=body)
        self.mailer.send(message)
        log.info('sent: %s' % message.to_message().as_string())

AnnotationNotifier.register_template('reply_notification', ReplyTemplate.generate_notification)
AnnotationNotifier.register_template('custom_search', CustomSearchTemplate.generate_notification)


@subscriber(events.AnnotationEvent)
def send_notifications(event):
    try:
        action = event.action
        request = event.request
        notifier = AnnotationNotifier(request)
        annotation = event.annotation
        annotation['parent'] = parent_values(annotation, request)

        queries = models.UserSubscriptions.get_all(request).all()
        for query in queries:
            # Do not do anything for disabled queries
            if not query.active: continue

            if FilterHandler(query.query).match(annotation, action):
                # Send it to the template renderer, using the stored template type
                notifier.send_notification_to_owner(annotation, {}, query.template)
    except:
        log.info(traceback.format_exc())
        log.info('Unexpected error occurred in send_notifications(): ' + str(event))


def generate_system_reply_query(username, domain):
    return {
        "match_policy": "include_all",
        "clauses": [
            {
                "field": "/references",
                "operator": "leng",
                "value": 0,
                "case_sensitive": True
            },
            {
                "field": "/parent/user",
                "operator": "equals",
                "value": 'acct:' + username + '@' + domain,
                "case_sensitive": True
            }
        ],
        "actions": {
            "create": True,
            "update": False,
            "delete": False
        },
        "past_data": {
            "load_past": "none"
        }
    }


def create_system_reply_query(user, domain, session):
    reply_filter = generate_system_reply_query(user.username, domain)

    query = models.UserSubscriptions(username=user.username)
    query.query = reply_filter
    query.template = 'reply_notification'
    query.type = 'system'
    query.description = 'Reply notification'
    session.add(query)


def create_default_subscription(request, user):
    session = get_session(request)
    url_struct = urlparse(request.application_url)
    domain = url_struct.hostname if len(url_struct.hostname) > 0 else url_struct.path
    create_system_reply_query(user, domain, session)

    # Added all subscriptions, write it to DB
    user.subscriptions = True
    session.add(user)
    session.flush()


@subscriber(events.NewRegistrationEvent)
def registration_subscriptions(event):
    create_default_subscription(event.request, event.user)


@subscriber(events.LoginEvent)
def login_subscriptions(event):
    if event.user:
        if not event.user.subscriptions:
            create_default_subscription(event.request, event.user)


def includeme(config):
    config.scan(__name__)
