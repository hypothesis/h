:orphan:

Architecture decision records
=============================

Here you will find documents which describe significant architectural decisions
made or proposed when developing the Hypothesis software. We record these in
order to provide a reference for the history, motivation, and rationale for past
decisions.

ADRs
----

.. toctree::
   :maxdepth: 1
   :glob:

   adr-*

What are ADRs?
--------------

Quoting from the `blog post which inspired this repository`_, an architecture
decision record, or ADR, is:

    ...a short text file in a [specific] format...[which] describes a set of
    forces and a single decision in response to those forces. Note that the
    decision is the central piece here, so specific forces may appear in
    multiple ADRs.

The standard sections of an ADR are:

    **Title** These documents have names that are short noun phrases. For
    example, "ADR 1: Deployment on Ruby on Rails 3.0.10" or "ADR 9: LDAP for
    Multitenant Integration"

    **Context** This section describes the forces at play, including
    technological, political, social, and project local. These forces are
    probably in tension, and should be called out as such. The language in this
    section is value-neutral. It is simply describing facts.

    **Decision** This section describes our response to these forces. It is
    stated in full sentences, with active voice. "We will ..."

    **Status** A decision may be "proposed" if the project stakeholders haven't
    agreed with it yet, or "accepted" once it is agreed. If a later ADR changes
    or reverses a decision, it may be marked as "deprecated" or "superseded"
    with a reference to its replacement.

    **Consequences** This section describes the resulting context, after
    applying the decision. All consequences should be listed here, not just the
    "positive" ones. A particular decision may have positive, negative, and
    neutral consequences, but all of them affect the team and project in the
    future.

.. _blog post which inspired this repository: http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions
