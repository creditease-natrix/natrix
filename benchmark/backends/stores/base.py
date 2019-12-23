

class BaseStoreClient:

    def put(self, event_data):
        raise NotImplemented()

    def puts(self, events):
        raise NotImplemented()
