from flask import Blueprint,g, abort
from flask import Response, request
import json

import logging
log = logging.getLogger('displayer')

displayer = Blueprint('displayer', __name__)

def jsonify(obj, *args, **kwargs):
    res = json.dumps(obj, indent=None if request.is_xhr else 2)
    return Response(res, mimetype='application/json', *args, **kwargs)

@displayer.route('/<id>')
def display_annotation(id):
  #return 'Howdy annotation ' + id + '!'
  resp = g.annotation_class.fetch(id)
  if not resp : 
    abort(404)
  return jsonify(resp)