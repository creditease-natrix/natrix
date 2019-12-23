
from django.conf import settings

from .eventhub import EventhubClient


store_type = settings.BENCHMARK_STORE_TYPE


# todo: move to initialize command
if store_type == 'eventhub':
    store_url = settings.BENCHMARK_STORE_URL
    eventhub_client = EventhubClient(service_url=store_url)
    # eventhub_client.init_store_service()

else:
    ...
