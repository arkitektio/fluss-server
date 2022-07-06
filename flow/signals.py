from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver
from flow.models import RunEvent, RunLog
import logging


@receiver(post_save, sender=RunEvent)
def samp_post_save(sender, instance=None, created=None, **kwargs):
    from flow.graphql.subscriptions import EventsSubscription

    EventsSubscription.broadcast(
        {"action": "created", "data": instance}
        if created
        else {"action": "updated", "data": instance},
        [EventsSubscription.RUNGROUP(instance.run)],
    )
    logging.info("SENDING EVENT")
