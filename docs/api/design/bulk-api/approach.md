# Approach and attitude

# Overview

This document covers the general approach being followed here, along with 
some beliefs and assumptions about the right way to go about APIs.

## Approach

When designing the API we should think about things we need:

 * Right now - so we can implement them
 * Things we might want in future - so we don't rule them out of make them awkward

Just because something is designed or discussed here _does not_ imply we intend
to actually implement it now. Features like this will be marked with "_(future)_".

## Attitude

_Warning! Personal opinions ahead!_

### An API you can use is the best API

An API that people can call is better than one which follows all current 
"best" practice.

For example:

Requesting different resources should be done with `Accept` 
headers, but they are totally impossible to send with raw HTML links. Therefore
a totally acceptable alternative is to also accept `?accept=` as query 
parameter rather than requiring the consumer to make all calls with Javascript.

... or:

Yes technically, the correct thing to do might be to have a `GET` with a JSON
body, but 50% of your customers won't be able to make that request with the
tools they are familiar with.

### Consumer comfort is important, but not paramount

We should make affordances that make our consumers lives better where we can
but not to the point it starts making our lives horrible.

This is for a couple of reasons:

 * Sometimes the trade off on our end is out of proportion to the benefit
   the user derives
   * Often you are your own user first and foremost, so seek a global minimum
 * 90% of the pain of calling an API for the average customer is getting someone
   who has any relevant skills to do it
   * Whether you require that person to order one thing before another isn't a 
     big slice of the pie
 * We are not serving our customers well by:
   * Creating fragile and complicated code
   * Deliving one "perfect" end-point rather than two good ones

This is not licence to be horrible: common sense is required in both directions.

### There's a lot of horrible cruft out there about JSON and REST APIs

 * A lot of the "rules" out there are just strongly worded opinions
 * Surpisingly few seem to benefit users, or address something users care about
 * Most fancy JSON language variants and tools have very little traction
   * JSON patch is not by any stretch of the imagination a standard (any of them)
   * HAL, HATEOAS and friends are kind of worse than not doing it, and nobody can consume it
   * A user won't thank you if the first step of learning your API is to go 
     learn another un-related language or paradigm

There are some good things to stick by:

 * __Good old fashioned HTTP semantics are good!__ (use them where you can)
 * JSON schema has decent cross language library support and uptake in other projects (like Swagger) 