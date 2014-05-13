from spotify.hermes.cache import HermesCache
from spotify.mercury.request import MercuryRequest


cache = HermesCache()


class HermesRequest(MercuryRequest):
    def __init__(self, sp, requests, schema, header=None, defaults=None):
        super(HermesRequest, self).__init__(
            sp, 'sp/hm_b64',
            requests, schema,
            header, defaults
        )

    def cached_response(self, request):
        cache_obj = cache.get(request.uri)

        if cache_obj is None:
            self.response[request.uri] = None
            return False

        self.response[request.uri] = (
            cache_obj.content_type,
            cache_obj.internal
        )

        return True

    def update_response(self, header, content_type, internal):
        uri = cache.get_object_uri(content_type, internal)

        if uri is None:
            raise NotImplementedError()

        # Update response
        self.response[uri] = (content_type, internal)

        # Store in cache for later use
        cache.store(header, content_type, internal)
