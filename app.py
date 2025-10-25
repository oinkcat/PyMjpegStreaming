import os
import re
import sys
import shutil
import bottle
from bottle import request, get, post, template

UPLOAD_DIR = './photos'
ALLOWED_MIME = 'image/jpeg'
ALLOWED_EXT = '.jpg'

@get('/')
@get('/<photo_idx:int>')
def viewer(photo_idx=0):
    """ Renders a viewer page. """

    all_photos = list_photos()
    has_photos = len(all_photos) > 0
    has_next = photo_idx < len(all_photos) - 1
    has_prev = photo_idx > 0

    return template('./index.html', \
        show=has_photos, has_prev=has_prev, has_next=has_next, \
        idx=photo_idx, total=len(all_photos))

def list_photos():
    return list(filter(lambda fn: fn.endswith(ALLOWED_EXT), os.listdir(UPLOAD_DIR)))

@get('/photo/<index:int>')
def download_photo(index):
    filename_from_end = list_photos()[-(index + 1)]
    return bottle.static_file(filename_from_end, UPLOAD_DIR)

@post('/upload')
def upload_photo():
    """ Upload photo endpoint """

    if request.content_length > 0 and request.content_type == ALLOWED_MIME:
        save_filename = os.path.join( \
            UPLOAD_DIR, \
            'p_{0}.jpg'.format(str(len(os.listdir(UPLOAD_DIR))).zfill(10))
        )

        with request.body as upload_f:
            with open(save_filename, 'wb') as save_f:
                shutil.copyfileobj(upload_f, save_f)

        return 'OK'
    else:
        bottle.abort(400, 'No file for upload')


if __name__ == '__main__':
    bottle.debug(True)

    # Starts a local test server.
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    PORT = os.environ.get('SERVER_PORT', '5555')
    bottle.run(server='wsgiref', host=HOST, port=PORT)
