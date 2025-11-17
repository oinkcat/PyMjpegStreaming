"""
Test MJPEG Streaming
"""
import os
import time
import socket
import bottle
from bottle import get, response
from threading import Thread, Event

class MjpegStreamGenerator:
    """ Creates HTTP stream frames from JPEG data """
    
    BOUNDARY = 'my_boundary'

    _frame_wait = Event()
    _running = True
    _frame_bytes = []

    _boundary_bytes = bytes(f"--{BOUNDARY}", 'ascii')
    _content_type_bytes = bytes('Content-Type: image/jpeg', 'ascii')

    def get_next_frame_part(self):
        """ Get next MGPEG frame for streaming """

        while True:
            MjpegStreamGenerator._frame_wait.wait()

            frame_bytes = MjpegStreamGenerator._frame_bytes
            content_length_bytes = bytes(f'Content-Length: {len(frame_bytes)}', 'ascii')

            yield b'\r\n'.join([
                    MjpegStreamGenerator._boundary_bytes, 
                    MjpegStreamGenerator._content_type_bytes,
                    content_length_bytes,
                    bytes(),
                    frame_bytes,
                    bytes()
                ])
            
            if MjpegStreamGenerator._running:
                MjpegStreamGenerator._frame_wait.clear()
            else:
                break

        yield f'--{MjpegStreamGenerator.BOUNDARY}--'

    @staticmethod
    def publish_frame(frame_bytes):
        """ Store frame bytes and notify waiting threads """

        if frame_bytes is not None:
            MjpegStreamGenerator._frame_bytes = frame_bytes
        else:
            MjpegStreamGenerator._running = False

        MjpegStreamGenerator._frame_wait.set()

class MjpegTcpListener:
    """ Listen for MJPEG stream and split frames """

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.thread = None

    def run(self):
        """ Start server thread """
        
        self.thread = Thread(target=self._serve)
        self.thread.start()

        print(f'Starting stream listener on: {self.host}:{self.port}')

    def _serve(self):
        """ Listen for incoming stream and serve client requests """

        splitter = BinarySplitter(self._got_frame, JPEG_HEADER, JPEG_TRAILER)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.host, self.port))
            server_socket.listen()

            while True:
                client_socket, addr_info = server_socket.accept()
                print(f'Connected stream client from: {addr_info}')

                with client_socket:
                    while recv_data := client_socket.recv(BS):
                        splitter.process(recv_data)
                        time.sleep(0.05)

                print('Client disconnected')

    def _got_frame(self, frame_bytes):
        MjpegStreamGenerator.publish_frame(frame_bytes)

    def stop(self):
        self.thread.join()

class BinarySplitter:
    """ Splits binary stream and yields frame data """

    def __init__(self, func, header, trailer):
        self._header = header
        self._trailer = trailer
        self.callback = func
        self.buffer = bytearray()
        self.hdr_pos = -1

    def is_header_found(self):
        return self.hdr_pos >= 0

    def process(self, chunk):
        self.buffer.extend(chunk)

        if not self.is_header_found():
            self.hdr_pos = self.buffer.find(self._header)

        if self.is_header_found():
            tr_pos = self.buffer.find(self._trailer)

            if tr_pos > -1:
                end_pos = tr_pos + len(self._trailer)
                self.callback(self.buffer[self.hdr_pos:end_pos])
                self.buffer = self.buffer[end_pos:]
                self.hdr_pos = -1

VIDEO_PATH = 'D:\\Temp\\MJPG\\camera.mjpeg'
MJPEG_MIME = 'multipart/x-mixed-replace'

BS = 4096

JPEG_HEADER = b'\xff\xd8\xff'
JPEG_TRAILER = b'\xff\xd9'

STREAM_LISTENER_HOST = 'localhost'
STREAM_LISTENER_PORT = 5566

@get('/')
def stream_mjpeg():
    """ Stream MJPEG from images in directory """

    response.content_type = f'{MJPEG_MIME}; boundary={MjpegStreamGenerator.BOUNDARY}'
    response.add_header('Cache-Control', 'no-cache')

    stream_generator = MjpegStreamGenerator()

    return stream_generator.get_next_frame_part()

def read_and_send_frames():
    """ Read frames from images and send to clients """

    def got_frame(frame_bytes):
        MjpegStreamGenerator.publish_frame(frame_bytes)
        time.sleep(0.1)

    splitter = BinarySplitter(got_frame, JPEG_HEADER, JPEG_TRAILER)

    with open(VIDEO_PATH, 'rb') as video_f:
        while chunk := video_f.read(BS):
            splitter.process(chunk)

    MjpegStreamGenerator.publish_frame(None)

if __name__ == '__main__':
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    PORT = int(os.environ.get('SERVER_PORT', '5555'))

    stream_server = MjpegTcpListener(HOST, STREAM_LISTENER_PORT)
    stream_server.run()
    
    bottle.debug(True)
    bottle.run(server='wsgiref', host=HOST, port=PORT)
    stream_server.stop()
