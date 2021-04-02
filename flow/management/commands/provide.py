from delt.bridge import arkitekt
from flow.models import FlowTemplate
from re import template
from pydantic import BaseModel
from django.core.management import BaseCommand
from bergen.messages.postman.provide import *
from bergen.clients.provider import ProviderBergen
import asyncio
import logging 
from asgiref.sync import sync_to_async
logger = logging.getLogger(__name__)

async def main():
    # Perform connection
    async with ProviderBergen(
        force_new_token=True,
        auto_reconnect=True# if we want to specifically only use pods on this innstance we would use that it in the selector
        ) as client:

        @client.hook("bounced_provide", overwrite=True)
        async def on_bounced_provide(self, bounced_provide: BouncedProvideMessage):
            
            template = await sync_to_async(FlowTemplate.objects.get)(arkitekt_id=bounced_provide.data.template)
            logger.error(template)



        await client.provide_async()



class Command(BaseCommand):
    help = "Starts the provider"
    leave_locale_alone = True

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)


    def handle(self, *args, **options):

        # Get the backend to use
        
        loop = asyncio.get_event_loop()
        loop.create_task(main())

        # we enter a never-ending loop that waits for data
        # and runs callbacks whenever necessary.
        print(" [x] Awaiting Providing requests")
        loop.run_forever()