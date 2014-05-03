from spotify.components.base import Component
from spotify.core.request import Request

from pyemitter import Emitter
from threading import Lock
from ws4py.client.threadedclient import WebSocketClient
import json
import logging

log = logging.getLogger(__name__)


class Connection(Component, Emitter):
    def __init__(self, sp):
        super(Connection, self).__init__(sp)

        self.client = None
        self.connected = False

        self.seq = 0
        self.requests = {}

        self.send_lock = Lock()

    def connect(self, url):
        if self.client:
            return

        self.seq = 0
        self.requests = {}

        self.client = Client(self, url)\
            .on('open', self.on_open)\
            .on('message', self.on_message)\
            .on('close', self.on_close)

        log.info('Connecting to "%s"' % url)

        self.client.connect()

    def disconnect(self):
        raise NotImplementedError()

    def on_open(self):
        log.debug('WebSocket "open" event')

        if not self.connected:
            self.send_connect()

    def on_message(self, message):
        # Parse json message
        try:
            data = json.loads(message.data)
        except ValueError, e:
            self.emit('error', 'Unable to decode message: %s' % e)
            return

        # Handle commands (do_work, ping_flash2, etc..)
        if 'message' in data:
            return self.emit('command', *data['message'])

        mid = data.get('id')

        # Request doesn't exist
        if mid not in self.requests:
            log.warn('Unhandled message received with id %s' % mid)
            return

        request = self.requests[mid]

        # Delete request from map, not needed anymore
        del self.requests[mid]

        # Process the response (fire callbacks)
        request.process(data)

    def on_close(self, code, reason=None):
        log.debug('WebSocket "close" event')

        if self.connected:
            self.disconnect()

    def send(self, name, *args):
        return self.build(name, *args)\
                   .send()

    def build(self, name, *args):
        return Request(self.sp, name, args)

    def send_request(self, request):
        # Build message
        message = request.build(self.seq)

        # Store request (to trigger callback on response)
        self.requests[self.seq] = request
        self.seq += 1

        # Build and send request
        self.send_message(message)

        return request

    def send_message(self, message):
        encoded = json.dumps(message, separators=(',', ':'))
        log.debug('send encoded: %s' % repr(encoded))

        with self.send_lock:
            self.client.send(encoded)

    def send_connect(self):
        log.debug('send_connect()')

        args = self.sp.config['credentials'][0].split(':', 2)
        args[2] = args[2].decode('string_escape')

        self.build('connect', *args)\
            .on('success', self.on_connect)\
            .send()
        # TODO .pipe('error', self)

    def on_connect(self, message):
        log.debug('SpotifyConnection "connect" event: %s', message)

        if message.get('result') == 'ok':
            log.debug('connected')
            self.connected = True

            return self.emit('connect')

        # TODO: handle possible error case
        log.error('handled error case')


class Client(WebSocketClient, Emitter):
    def __init__(self, connection, *args, **kwargs):
        WebSocketClient.__init__(self, *args, **kwargs)
        self._connection = connection

        self.daemon = True

    def opened(self):
        self.emit('open')

    def received_message(self, message):
        self.emit('message', message=message)

    def closed(self, code, reason=None):
        self.emit('close', code=code, reason=reason)
