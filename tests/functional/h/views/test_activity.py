# Permission.Group.ADMIN
# The `group_edit_url` should be visible for those with edit permissions
# OAuth clients, staff and admins can edit a group
# The creator of thr group can also edit the group


# Permission.Group.JOIN / Permission.Group.READ
# If the group is world readable, any logged in user can read
# If the group is readable by members, any logged in user in the group can read
# An OAuth client can read those in the same authority

# If you don't have permissions to read a group and you are either:
#  * Not logged in
#  * ... or are and have the JOIN permission
# The  template rendered is changed to "h:templates/groups/join.html.jinja2"

# A user has the JOIN permission if a group is marked as joinable by authority,
# they are logged in user and in the right authority
