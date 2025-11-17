"""
Test JPEG Sequence Streaming
"""
import os
import shutil
import bottle
import threading
from bottle import request, get, post, response, template
from io import BytesIO

class PhotoUploadStorage:
    """ Storage implemented as file system directories """

    SUBDIR_CAPACITY = 1000
    FILE_TEMPLATE = 'p_{0}.jpg'

    def __init__(self, path):
        self.base_path = path

    def get_photos_count(self):
        """ Get total number of photos """

        segments = self.get_segments_list()
    
        if len(segments) > 0:
            num_photos_rest = len(os.listdir(os.path.join(UPLOAD_DIR, str(segments[-1]))))
            return (len(segments) - 1) * PhotoUploadStorage.SUBDIR_CAPACITY + num_photos_rest
        else:
            return 0

    def get_segments_list(self):
        """ Return ordered list of segments (subdirectories) """

        return sorted([int(n) for n in os.listdir(self.base_path) if n.isnumeric()])

    def get_photo_path_by_idx(self, index):
        """ Return path to photo with specified index """

        file_name = self.get_photo_filename(index)
        segment_idx = index // PhotoUploadStorage.SUBDIR_CAPACITY
        segment_dir = str(segment_idx).zfill(5)
        photo_path = os.path.join(self.base_path, segment_dir, file_name)

        return photo_path if os.path.isfile(photo_path) else None

    def get_photo_filename(self, index):
        """ Get formatted name of photo for given index """

        return PhotoUploadStorage.FILE_TEMPLATE.format(str(index).zfill(10))

    def save_new_photo_fileobj(self, fileobj):
        """ Save contents of file-like object as new photo """

        new_photo_idx = self.get_photos_count()
        segment_idx = new_photo_idx // PhotoUploadStorage.SUBDIR_CAPACITY
        subdir_path = os.path.join(UPLOAD_DIR, str(segment_idx))

        if not os.path.isdir(subdir_path):
            os.mkdir(subdir_path)

        new_photo_name = self.get_photo_filename(new_photo_idx)
        new_photo_path = os.path.join(subdir_path, new_photo_name)

        with open(new_photo_path, 'wb') as save_f:
            shutil.copyfileobj(fileobj, save_f)

class PhotoMemoryCache:
    """ Caches photo bytes in memory """

    def __init__(self):
        self.photo_io = BytesIO()
        self.lock = threading.Lock()
  
    def read_photo(self):
        """ Read last photo bytes from cache """

        with self.lock:
            self.photo_io.seek(0)
            photo_data = self.photo_io.read()

            return photo_data

    def write_photo(self, fileobj):
        """ Write photo bytes into cache from file-like object """

        with self.lock:
            self.photo_io.seek(0)
            self.photo_io.truncate(0)
            shutil.copyfileobj(fileobj, self.photo_io)

# Upload settings
UPLOAD_DIR = './photos'
ALLOWED_MIME = 'image/jpeg'
ALLOWED_EXT = '.jpg'

storage = PhotoUploadStorage(UPLOAD_DIR)
last_photo_cache = PhotoMemoryCache()

@get('/')
@get('/<photo_idx:int>')
def viewer(photo_idx=0):
    """ Renders a viewer page. """

    total_num_photos = storage.get_photos_count()
    has_photos = total_num_photos > 0
    has_next = photo_idx < total_num_photos - 1
    has_prev = photo_idx > 0
    
    is_static = 'static' in request.GET and request.GET['static'] == '1'

    return template('./index.html', \
        show=has_photos, has_prev=has_prev, has_next=has_next, \
        idx=photo_idx, total=total_num_photos, \
        static=is_static)

@get('/photo/<index:int>')
def download_photo(index):
    """ Send captured photo """

    total_num_photos = storage.get_photos_count()
    photo_path = storage.get_photo_path_by_idx(total_num_photos - index - 1)

    if photo_path is not None:
        photo_dir, photo_name = os.path.split(photo_path)
        return bottle.static_file(photo_name, photo_dir)
    else:
        bottle.abort(404, 'No photo exists')

@get('/photo/latest')
def download_latest_photo():
    """ Send latest cached captured photo """

    cached_photo_bytes = last_photo_cache.read_photo()

    if len(cached_photo_bytes) > 0:
        response.content_type = ALLOWED_EXT
        return cached_photo_bytes
    else:
        return download_photo(0)

@post('/upload')
def upload_photo():
    """ Upload photo endpoint """

    if request.content_length > 0 and request.content_type == ALLOWED_MIME:
        with request.body as upload_f:
            # Cache last uploaded photo
            last_photo_cache.write_photo(request.body)

            # Save to upload directory
            upload_f.seek(0)
            storage.save_new_photo_fileobj(upload_f)

        return 'OK'
    else:
        bottle.abort(400, 'No file for upload')

if __name__ == '__main__':
    bottle.debug(True)

    # Starts a local test server.
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    PORT = os.environ.get('SERVER_PORT', '5555')
    bottle.run(server='wsgiref', host=HOST, port=PORT)
