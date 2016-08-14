# coding=utf-8
import random
import string

from datetime import timedelta

import simplejson
from django.contrib.auth import models as auth_models
from django.db import models
from jsonfield import JSONField


class BaseModel(models.Model):
    """
    Base model from which all other models should inherit. It has a unique key and other nice fields, like a unique id.
    If you override this class, you should probably add more unique identifiers, like a uuid or hash or something.
    """
    id = models.AutoField(primary_key=True)
    key = models.CharField(max_length=10, unique=True, db_index=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    @staticmethod
    def key_generator(length=10, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(length))

    def generate_key(self, length=10):
        if not self.key:
            for _ in range(10):
                key = self.key_generator(length)
                if not type(self).objects.filter(key=key).count():
                    self.key = key
                    break

    def save(self, *args, **kwargs):
        self.generate_key()
        super(BaseModel, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class UserBackend(object):
    @staticmethod
    def authenticate(email=None, uuid=None):
        try:
            user = OpenBadgeUser.objects.get(email=email)

            if user.email != email:
                return None

        except OpenBadgeUser.DoesNotExist:
            user = OpenBadgeUser(email=email, phone_uuid=uuid, username=email)
            user.save()
        except OpenBadgeUser.MultipleObjectsReturned:
            return None

        return user

    @staticmethod
    def get_user(user_id):
        try:
            return OpenBadgeUser.objects.get(pk=user_id)
        except OpenBadgeUser.DoesNotExist:
            return None


def fix_email(cls):
    field = cls._meta.get_field('email')
    field.required = True
    field.blank = False
    field._unique = True
    field.db_index = True

    return cls


@fix_email
class OpenBadgeUser(auth_models.AbstractUser, BaseModel):
    pass


class Project(BaseModel):
    """
    Definition of the Project, which is an `organization`-level collection of hubs, badges, and meetings
    """

    name = models.CharField(max_length=64)

    def __unicode__(self):
        return self.name

    def get_all_meetings(self, get_file):
        return {'meetings': {meeting.uuid: meeting.to_object(get_file) for meeting in self.meetings.all()}}

    def to_object(self, hub):
        """
        this should be things that are relatively constant, and won't need to be updated mid-meeting
        """

        return {
            'project': {
                'id': self.id,
                'key': self.key,
                'name': self.name,
                'badge_map': {member.badge: {"name": member.name, "key": member.key} for member in self.members.all()},
                'members': {member.name: member.to_object() for member in self.members.all()},
                'active_meetings': [meeting.metadata.data for meeting in self.meetings.all()
                                        if meeting.metadata.data['is_active']]
            },
            'hub': {
                "name": hub.name,
                "last_updates": {meeting.uuid: meeting.get_last_log_index_for_hub(hub)
                                 for meeting in hub.get_meetings()},
                "su": hub.su
            }
        }


class Hub(BaseModel):
    """Definition of a Hub, which is owned by a Project and has am externally generated uuid"""

    name = models.CharField(max_length=64)

    project = models.ForeignKey(Project, null=True, related_name="hubs", on_delete=models.CASCADE)

    current_meeting = models.ForeignKey('Meeting', null=True, blank=True, related_name="hubs", on_delete=models.SET_NULL)

    su = models.BooleanField(default=False)
    """Is this a Super User? Gets updated mid-meeting."""

    uuid = models.CharField(max_length=64, db_index=True, unique=True)
    """ng-device generated uuid"""

    def get_meetings(self):
        meetings = []
        for meeting in self.project.meetings.all():
            metadata = meeting.metadata.data
            if self.uuid in metadata['hubs']:
                meetings.append(meeting)
        return meetings

    def to_object(self, last_update=0):
        """
        These are all the things that change as the meeting progresses. Mainly the last_update for the hub.
        """
        return {"last_update": self.current_meeting.get_last_log_index_for_hub(self) if self.current_meeting else None,
                "badge_map":{member.badge: {"name": member.name, "key": member.key}
                             for member in self.project.members.all()
                             if int(member.date_updated.strftime("%s")) > last_update},
                "meeting":self.current_meeting.metadata.data if self.current_meeting else None,
                "su": self.su}

    def __unicode__(self):
        return self.name


class Member(BaseModel):
    """Definition of a Member, who belongs to a Project, and owns a badge"""

    class Meta:
        unique_together = ['badge', 'project']

    name = models.CharField(max_length=64)
    email = models.EmailField(unique=False, blank=True)
    badge = models.CharField(max_length=64)
    """Some sort of hub-readable ID for the badge, similar to a MAC, but accessible from iPhone"""

    project = models.ForeignKey(Project, related_name="members", on_delete=models.CASCADE)

    def to_object(self):
        return {'id':self.id, 'name':self.name, 'badge':self.badge}

    def __unicode__(self):
        return self.name



class Meeting(BaseModel):
    """
    Represents a Meeting, which belongs to a Project, and has a log_file and a last_update_time, among other standard
    metadata
    """

    version = models.DecimalField(decimal_places=2, max_digits=5)
    """The logging version this project uses"""

    uuid = models.CharField(max_length=64, db_index=True, unique=True)
    """something like [project_name]|[start_time], start time in ms, making it infeasible to `hack`"""

    # Meta type data
    metadata = models.ForeignKey('Event', related_name="none", null=True, on_delete=models.CASCADE)

    project = models.ForeignKey(Project, related_name="meetings", on_delete=models.CASCADE)
    """The Project this Meeting belongs to"""

    def duration(self):
        if self.get_meta('end_time'):
            timedelta(seconds=int(self.get_meta('end_time') - self.get_meta('start_time')))
        return timedelta(seconds=int(float(self.events.latest().log_timestamp) - self.get_meta('start_time')))

    def __unicode__(self):
        return unicode(self.project.name) + "|" + str(self.get_meta('start_time'))

    def get_meta(self, property=None):
        if property:
            try:
                return self.metadata.data[property]
            except KeyError:
                return None

        return self.metadata.data

    def get_events(self, hub = None):
        """get all events, optionally by hub"""
        if hub:
            return self.events.filter(hub=hub)
        else:
            return self.events.all()

    def get_last_log_index_for_hub(self, hub):
        try:
            return self.get_events(hub).latest().log_index
        except Event.DoesNotExist:
            return -1

    def to_object(self, get_file = False):
        """Get an representation of this object for use with HTTP responses"""

        if get_file:
            return {"events": [event.to_object() for event in self.get_events()],
                    "metadata":self.metadata.data}

        return {"metadata": self.metadata.data}


class Event(models.Model):
    """
    Represents a piece of data uploaded by the phone. Could be anything from meeting starts to accelerometer data
    """

    uuid = models.CharField(max_length=128, primary_key=True)
    """Concatenation of meeting key, hub uuid, and log_index"""

    type = models.CharField(max_length=64)
    """What kind of event this is: meeting start, audio receive, etc"""

    log_timestamp = models.DecimalField(decimal_places=3, max_digits=20)
    """When the phone saved this log"""

    log_index = models.IntegerField()
    """Chronological ordering of the logs -- by hub!"""

    hub = models.ForeignKey(Hub, related_name="events", null=True, on_delete=models.SET_NULL)
    """Which hub recorded this event"""

    data = JSONField(null=True, blank=True)
    """Whatever other data there is about this event"""

    meeting = models.ForeignKey(Meeting, related_name="events", on_delete=models.CASCADE)
    """What meeting this is a part of"""

    def to_object(self):
        """This returns a dict that's basically the same format as a log line"""
        return {
            'type':self.type,
            'log_timestamp':self.log_timestamp,
            'log_index':self.log_index,
            'hub':self.hub.uuid,
            'data':self.data
        }

    def to_json(self):
        """This returns a string that's basically the same format as a log line"""
        return simplejson.dumps(self.to_object())

    def __unicode__(self):
        return self.type + "@" + self.uuid

    class Meta:
        ordering = ['log_timestamp']
        get_latest_by = 'log_index'