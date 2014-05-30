from spotify.components.base import Component
from spotify.hermes.request import HermesRequest
from spotify.core.uri import Uri
from spotify.objects import Album, Track, Artist, Playlist

import logging
import urllib

log = logging.getLogger(__name__)


class Metadata(Component):
    def get(self, uris, callback=None):
        log.debug('metadata(%s)', uris)

        if type(uris) is not list:
            uris = [uris]

        # array of "request" Objects that will be protobuf'd
        requests = []
        h_type = ''

        for uri in uris:
            if type(uri) is not Uri:
                uri = Uri.from_uri(uri)

            if uri.type == 'local':
                log.debug('ignoring "local" track URI: %s', uri)
                continue

            h_type = uri.type

            requests.append({
                'method': 'GET',
                'uri': 'hm://metadata/%s/%s' % (uri.type, uri.to_id())
            })

        # Build ProtoRequest
        request = HermesRequest(self.sp, requests, {
            'vnd.spotify/metadata-artist': Artist,
            'vnd.spotify/metadata-album': Album,
            'vnd.spotify/metadata-track': Track
        }, {
            'method': 'GET',
            'uri': 'hm://metadata/%ss' % h_type
        })

        return self.request_wrapper(request, callback)

    def playlist(self, uri, start=0, count=100, callback=None):
        parts = str(uri).split(':')

        request = HermesRequest(self.sp, {
            'method': 'GET',
            'uri': 'hm://playlist/%s?from=%s&length=%s' % ('/'.join(parts[1:]), start, count)
        }, Playlist, defaults={
            'uri': Uri.from_uri(uri)
        })

        return self.request_wrapper(request, callback)

    def playlists(self, username, start=0, count=100, callback=None):
        if count > 100:
            raise ValueError("You may only request up to 100 playlists at once")

        request = HermesRequest(self.sp, {
            'method': 'GET',
            'uri': 'hm://playlist/user/%s/rootlist?from=%s&length=%s' % (username, start, count)
        }, Playlist, defaults={
            'uri': Uri.from_uri('spotify:user:%s:rootlist' % username)
        })

        return self.request_wrapper(request, callback)

    def collection(self, username, source, params=None, callback=None):
        query = urllib.urlencode(params or {})

        request = HermesRequest(self.sp, {
            'method': 'GET',
            'uri': 'hm://collection-web/v1/%s/%s%s' % (username, source, query)
        }, {
            'album': Album,
            'artist': Artist
        })

        return self.request_wrapper(request, callback)
