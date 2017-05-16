============================
How to review a pull request
============================

This is our shared, collaborative how-to for reviewing a pull request at
Hypothesis. Like everything else in our documentation, this isn't set in stone
but is a living, collaborative document. If you want to question or change
something in this guide, open a GitHub issue or pull request.


-------------------
Aims of code review
-------------------

What we aim to achieve by code review at Hypothesis:

* Foster and enact a positive, patient and friendly internal culture for our
  team
* Improve working relationships between developers
* Relieve tension by giving positive feedback
* Learn from the code that you're reviewing
* Break down code silos, giving each member a broad exposure to different parts
  of the codebase
* Mentor and educate
* Find bugs and improve code quality

------
Don'ts
------

* Don't be blunt and just point out the things that are wrong and that you want
  changed, without saying anything else.

* Don't harshly criticize code, and don't use personal tone, hyperbole, or
  demanding, challenging, insulting, impatient or passive-aggressive language
  when criticizing code.

* Don't be a back-seat coder. Consider your suggestions carefully and pick the
  best ones.

* Don't break the rule of no surprises. Suggestions should be evidence-based
  not opinion-based. For example, based on our
  :doc:`documented coding standards <code-style>` rather than on conflicting
  opinions about trade-offs.

----
Do's
----

* Praise good code
* Ask, don't tell. Ask questions rather than making statements
* Ask questions, don't make demands
* Avoid accusatory *why* questions ("Why didn't you just <do what you think they should have done>?")
* When making a suggestion, also give the reason why you think the change
  might be an improvement
* Use the checklist below
* Refer to the :doc:`coding standards <code-style>`, and use them as the
  foundation of your review

---------
Checklist
---------

This is a checklist to follow before submitting your code for review,
and for the reviewer to use to know what to look for when reviewing:

* Your branch should contain one logically separate piece of work and not any
  unrelated changes

* You should have good commit messages, see
  http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html

* Your branch should contain new or changed tests for any new or changed code

* Your branch should be up to date with the master branch and mergeable without
  conflicts, so rebase your branch on top of master before submitting your pull
  request

* Any new code should follow our :doc:`coding standards <code-style>`

* If the new code contains changes to the database schema, it should include a
  database migration. See  :doc:`making-changes-to-model-code`

* Has the code been tested using production data?
  See ``<link to getting production data in development guide>``.

* If there are UI changes, have they been tested on different screen sizes and
  in different browsers? See ``<link to responsive design guide>``.

* If there are UI changes, do they meet our accessibility standards?
  See ``<link to accessibility guide>``.

* If there are new user-visible strings, are they internationalized?
  See ``<link to internationalization guide>``.
