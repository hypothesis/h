# Permission.Group.CREATE
# Any logged in user can create a group
# Logged out users should not be able to

# Permission.Group.READ / Permission.Group.MEMBER_READ
# If the group is world readable, any logged in user can read
# If the group is readable by members, any logged in user in the group can read
# An OAuth client can read those in the same authority

# Permission.Group.ADMIN
# OAuth clients, staff and admins can edit a group
# The creator of thr group can also edit the group

# Permission.Group.UPSERT
# The creator of thr group can upsert a group

# Permission.Group.MEMBER_ADD
# An OAuth client can add members to a group (nobody else?)
