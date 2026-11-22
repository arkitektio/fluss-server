import logging

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from kante.channel import CRUDSignal

from reaktion import channel_signals, channels, models

logger = logging.getLogger(__name__)


@receiver(post_save, sender=models.RunEvent)
def event_singal(sender, instance=None, **kwargs):
    if instance:
        logger.debug("RunEvent %s saved; broadcasting to run_%s", instance.id, instance.run_id)
        channels.run_event_channel.broadcast(channel_signals.RunEventSignal(event=instance.id), [f"run_{instance.run.id}"])


def _run_organization(run: models.Run) -> int | None:
    """The organization of a run, which it reaches only through its (nullable) flow."""
    if run.flow_id is None:
        return None
    return models.Flow.objects.filter(id=run.flow_id).values_list("organization_id", flat=True).first()


@receiver(post_save, sender=models.Run)
def run_saved(sender: type[models.Run], instance: models.Run, created: bool, raw: bool = False, **kwargs: object) -> None:
    """A run started, or changed status: told to its organization and its own room once committed."""
    if raw:
        return
    organization_id = _run_organization(instance)
    if organization_id is None:
        return
    signal = CRUDSignal(create=instance.id) if created else CRUDSignal(update=instance.id)
    channels.run_channel.broadcast_on_commit(signal, channels.run_groups(organization_id, instance.id))


@receiver(pre_delete, sender=models.Run)
def run_deleted(sender: type[models.Run], instance: models.Run, **kwargs: object) -> None:
    """A run is deleted: its organization is read now, while its flow still exists."""
    organization_id = _run_organization(instance)
    if organization_id is None:
        return
    channels.run_channel.broadcast_on_commit(CRUDSignal(delete=instance.id), channels.run_groups(organization_id, instance.id))


def _python_run_organization(run: models.PythonRun) -> int | None:
    return models.PythonFlow.objects.filter(id=run.flow_id).values_list("organization_id", flat=True).first()


@receiver(post_save, sender=models.PythonRun)
def python_run_saved(sender: type[models.PythonRun], instance: models.PythonRun, created: bool, raw: bool = False, **kwargs: object) -> None:
    """A Python run started, was reopened or finished: told once committed."""
    if raw:
        return
    organization_id = _python_run_organization(instance)
    if organization_id is None:
        return
    signal = CRUDSignal(create=instance.id) if created else CRUDSignal(update=instance.id)
    channels.python_run_channel.broadcast_on_commit(signal, channels.python_run_groups(organization_id, instance.id))


@receiver(pre_delete, sender=models.PythonRun)
def python_run_deleted(sender: type[models.PythonRun], instance: models.PythonRun, **kwargs: object) -> None:
    organization_id = _python_run_organization(instance)
    if organization_id is None:
        return
    channels.python_run_channel.broadcast_on_commit(CRUDSignal(delete=instance.id), channels.python_run_groups(organization_id, instance.id))
