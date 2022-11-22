Create dev users
----------------

This task is intended to be run as a once off should you scrub your DB in
development and need to add back the FDW users.

You need to run this script once to create the required users, after which the
normal tasks will maintain the permissions.

This is only intended to be run in dev and is mostly for the benefit of testing
upstream consumers of the tables via FDW.

This is a **dangerous** task:

 * It will empty the schema
 * It will drop permissions on users
