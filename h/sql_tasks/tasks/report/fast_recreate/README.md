Fast recreate
-------------

This task will partially re-create the reporting environment from its
definitions. This will not update anything which might take a long time and is
good for example, when changing materialized views.

This is a **dangerous** task:

 * It will disrupt reporting as it's run
 * It _shouldn't_ take any longer than a normal refresh
