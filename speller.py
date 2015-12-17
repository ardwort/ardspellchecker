import re, collections, json
from itertools import groupby
from datetime import timedelta
from flask import make_response, request, session, current_app, redirect, jsonify, Response, render_template
from flask.ext.compress import Compress
from  werkzeug.debug import get_current_traceback
from functools import update_wrapper, wraps
import itertools, time, os
import requests
from StringIO import StringIO
from flask import after_this_request, request
from cStringIO import StringIO as IO
from flask.ext.autodoc import Autodoc
from indonesian_stemmer import ILStemmer
import gzip
import functools
import logging
import os
import difflib
from logging.handlers import RotatingFileHandler
def gzipped(f):
    @functools.wraps(f)
    def view_func(*args, **kwargs):
        @after_this_request
        def zipper(response):
            accept_encoding = request.headers.get('Accept-Encoding', '')

            if 'gzip' not in accept_encoding.lower():
                return response

            response.direct_passthrough = False

            if (response.status_code < 200 or
                response.status_code >= 300 or
                'Content-Encoding' in response.headers):
                return response
            gzip_buffer = IO()
            gzip_file = gzip.GzipFile(mode='wb',
                                      fileobj=gzip_buffer)
            gzip_file.write(response.data)
            gzip_file.close()

            response.data = gzip_buffer.getvalue()
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Vary'] = 'Accept-Encoding'
            response.headers['Content-Length'] = len(response.data)

            return response

        return f(*args, **kwargs)

    return view_func

def support_jsonp(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            content = str(callback) + '(' + str(f().data) + ')'
            return current_app.response_class(content, mimetype='application/json')
        else:
            return f(*args, **kwargs)
    return decorated_function

from flask import Flask, url_for
app = Flask(__name__)
if app.debug is not True:
    import logging
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler('spellcheck.log', maxBytes=1024 * 1024 * 100, backupCount=20)
    file_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)

auto = Autodoc(app)

def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

def words(text): return re.findall('[a-z]+', text.lower()) 

NWORDS = json.loads(open('ardwordlist.json','r').read())
stem = ILStemmer()
@app.route('/', methods=['GET', 'POST'])
@crossdomain(origin='*')
def index():
    if request.method == "POST":
        action = request.values.get('action', None)
        if action:
            if action == 'get_incorrect_words':
                text = request.values.get('text[]', None)
                listword = words(text)
                unmatched_items = [d for d in listword if d not in NWORDS]
                true_unmatched = []
                baseword = None
                if len(unmatched_items) > 0:
                    for a in unmatched_items:
                        try:
                            stemmed = stem.stem_word(a)
                            for root,value in stemmed.items():
                                baseword = root
                        except:
                            baseword = None
                        if not baseword:
                            true_unmatched.append(a)
                result = {"outcome":"success","data":[true_unmatched]}
            elif action == 'get_suggestions':
                text = request.values.get('word', None)
                result = difflib.get_close_matches(text,NWORDS)
                return Response(json.dumps(result),  mimetype='application/json')
        else:
            result = {}
    else:
        result = {}
    return jsonify(result)



if __name__ == '__main__':
    app.secret_key = 'inimustidiisiapakirakirayaakujugandakbegitungertisih'
    app.run()

