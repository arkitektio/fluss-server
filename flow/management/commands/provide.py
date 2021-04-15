from bergen.schema import NodeType, Template
from flow.actors import FuncFlowActor, GenFlowActor
from django.core.management import BaseCommand
from bergen.messages.postman.provide import *
from bergen.clients.provider import ProviderBergen
import asyncio
import logging 
from bergen.messages import *
from bergen.provider.base import BaseProvider




logger = logging.getLogger(__name__)






async def main():
    # Perform connection
    async with ProviderBergen(
        force_new_token=True,
        auto_reconnect=True# if we want to specifically only use pods on this innstance we would use that it in the selector
        ) as client:

        @client.hook("get_actorclass_for_template", overwrite=True)
        async def get_actorclass_for_template(self: BaseProvider, template_id):
            template = await Template.asyncs.get(id=template_id)

            if template.node.type == NodeType.FUNCTION:
                return FuncFlowActor

            if template.node.type == NodeType.GENERATOR:
                return GenFlowActor



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