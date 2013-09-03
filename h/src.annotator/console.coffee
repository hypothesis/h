# Stub the console when not available so that everything still works.

functions = [
  "log", "debug", "info", "warn", "exception", "assert", "dir", "dirxml",
  "trace", "group", "groupEnd", "groupCollapsed", "time", "timeEnd", "profile",
  "profileEnd", "count", "clear", "table", "error", "notifyFirebug", "firebug",
  "userObjects"
]

if console?
  # Opera's console doesn't have a group function as of 2010-07-01
  if not console.group?
    console.group = (name) -> console.log "GROUP: ", name

  # Webkit's developer console has yet to implement groupCollapsed as of 2010-07-01
  if not console.groupCollapsed?
    console.groupCollapsed = console.group

  # Stub out any remaining functions
  for fn in functions
    if not console[fn]?
      console[fn] = -> console.log _t("Not implemented:") + " console.#{name}"
else
  this.console = {}

  for fn in functions
    this.console[fn] = ->

  this.console['error'] = (args...) ->
    alert("ERROR: #{args.join(', ')}")

  this.console['warn'] = (args...) ->
    alert("WARNING: #{args.join(', ')}")
