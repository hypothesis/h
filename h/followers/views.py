# coding=utf8
from pyramid import httpexceptions as exc
from pyramid.view import view_config
from pyramid import renderers
from h import i18n
from h import models

from h import util
from pyramid.compat import escape

from pyramid import security



_ = i18n.TranslationString


@view_config(route_name='follow',
             request_method='POST',
             renderer="string")
def post_follow(request):
    """ follow someone by user_id. """
    if request.authenticated_userid is None:
        raise exc.HTTPNotFound()

    try:
        json_body = request.json_body
    except ValueError as err:
        raise Exception(
            _('Could not parse request body as JSON: {message}'.format(
                message=err.message)))

    if not isinstance(json_body, dict):
        raise Exception(
            _('Request JSON body must have a top-level object'))

    username = unicode(json_body.get('username') or '')
    if not username:
        raise exc.HTTPNotFound()
    user = models.User.get_by_username(request.db, username)
    me = models.User.get_by_username(
        request.db,
        util.user.split_user(
            request.authenticated_userid)
                ['username']
    )
    if not user:
        raise exc.HTTPNotFound()

    follower = models.Follower.get_by_user_and_follower( request.db, me=me, follow=user)

    if follower:
        raise exc.HTTPNotAcceptable()


    follower = models.Follower( follow=user, me = me )
    request.db.add(follower)
    request.db.flush()

    return {'followed': username}

@view_config(route_name="follow",
             request_method="GET",
             renderer='h:templates/followers/followers.html.jinja2')
def get_follow(request):
    if request.authenticated_userid is None:
        raise exc.HTTPNotFound()
    render = lambda username : '''
            <script type="text/javascript" src="https://ajax.googleapis.com/ajax/libs/jquery/1.7.2/jquery.min.js"></script>
            <script>
            JSONTest = function() {{

            var resultDiv = $("#resultDivContainer");
            $.ajax({{
              type: "POST",
              url: "/follow",
              data: JSON.stringify({{"username":'{username}'}}),
              success: function(data){{
                  with(window.document) {{
                    open();
                    write(data);
                    close();
                    }}
                  }},
              error: function(xhr, textStatus, errorThrown) {{
                  with(window.document) {{
                    open();
                    write(xhr.responseText);
                    close();
                    }}
                  }},
            }});
            }}
            </script>
            <div id="resultDivContainer"></div>
            <button type="button" onclick="JSONTest()">Follow {username}</button>
    '''.format(**{'username':username})

    users = map(lambda x: x.username, models.User.get_a_list_of_all_users(request.db))

    my_username = util.user.split_user(request.authenticated_userid)['username']
    users.remove(my_username)

    me = models.User.get_by_username(request.db, my_username) 
    following_already = models.Follower.get_following(request.db, me)

    following_already_status = map (lambda x:
                            models.User.get_by_id(request.db, x.follow_id).username, following_already
                        )

    for user in users:
        if user in following_already_status:
            users.remove(user)

    rendered = map(lambda x: render(x), users)
    rendered = ''.join(rendered)
    return {'followers': rendered }


@view_config(route_name='unfollow',
             request_method='GET',
             renderer='h:templates/followers/followers.html.jinja2')
def get_unfollow(request):
    if request.authenticated_userid is None:
        raise exc.HTTPNotFound()
    render = lambda username : '''
            <script type="text/javascript" src="https://ajax.googleapis.com/ajax/libs/jquery/1.7.2/jquery.min.js"></script>
            <script>
            JSONTest = function() {{

            var resultDiv = $("#resultDivContainer");
            $.ajax({{
              type: "POST",
              url: "/unfollow",
              data: JSON.stringify({{"username":'{username}'}}),
              success: function(data){{
                  with(window.document) {{
                    open();
                    write(data);
                    close();
                    }}
                  }},
              error: function(xhr, textStatus, errorThrown) {{
                  with(window.document) {{
                    open();
                    write(xhr.responseText);
                    close();
                    }}
                  }},
            }});
            }}
            </script>
            <div id="resultDivContainer"></div>
            <button type="button" onclick="JSONTest()">Unfollow {username}</button>
    '''.format(**{'username':username})

    my_username = util.user.split_user(request.authenticated_userid)['username']
    me = models.User.get_by_username(request.db, my_username) 
    to_unfollow = models.Follower.get_following(request.db, me)
    to_unfollow_uids = map (lambda x:
                            models.User.get_by_id(request.db, x.follow_id).username,to_unfollow 
                        )
    rendered = map(lambda x: render(x), to_unfollow_uids)
    rendered = ''.join(rendered)
    return {'followers': rendered }

@view_config(route_name='unfollow',
             request_method='POST',
             renderer="string")
def post_unfollow(request):
    """ unfollow someone by user_id. """
    if request.authenticated_userid is None:
        raise exc.HTTPNotFound()

    try:
        json_body = request.json_body
    except ValueError as err:
        raise Exception(
            _('Could not parse request body as JSON: {message}'.format(
                message=err.message)))

    if not isinstance(json_body, dict):
        raise Exception(
            _('Request JSON body must have a top-level object'))

    username = unicode(json_body.get('username') or '')
    if not username:
        raise exc.HTTPNotFound()
    user = models.User.get_by_username(request.db, username)
    me = models.User.get_by_username(
        request.db,
        util.user.split_user(
            request.authenticated_userid)
                ['username']
    )

    if not user:
        raise exc.HTTPNotFound()

    follower = models.Follower.get_by_user_and_follower(request.db, me=me, follow=user)

    if not follower:
        raise exc.HTTPNotFound()

    request.db.delete(follower)
    request.db.flush()

    return {'unfollowed':username}


@view_config(route_name='followers',
             request_method='GET',
             renderer='h:templates/followers/followers.html.jinja2')
def get_followers(request):
    if request.authenticated_userid is None:
        raise exc.HTTPNotFound()
    uid = util.user.split_user(request.authenticated_userid)['username']
    me = models.User.get_by_username(request.db, uid)
    followers = models.Follower.get_followers(request.db, me)
    count = len(followers)
    follow_status = map(lambda x: (models.User.get_by_id(x.me_id).username), followers)
    return {'followers':follow_status}


@view_config(route_name='following',
             request_method='GET',
             renderer='h:templates/followers/following.html.jinja2')
def get_following(request):
    if request.authenticated_userid is None:
        raise exc.HTTPNotFound()

    uid = util.user.split_user(request.authenticated_userid)['username']
    me = models.User.get_by_username(request.db, uid)
    following = models.Follower.get_following(request.db, me)

    count = len(following)
    follow_status = map (lambda x:
                            models.User.get_by_id(request.db, x.follow_id).username, following
                        )

    return {'following':follow_status}


def includeme(config):
    config.add_route('follow', '/follow')
    config.add_route('unfollow', '/unfollow')
    config.add_route('followers', '/followers')
    config.add_route('following', '/following')
    # api endpoints
    config.scan(__name__)
