# coding=utf-8
import datetime
import os
import pytz
import random
import simplejson
import string

from django.conf import settings
from django.contrib.auth import models as auth_models
from django.core.files.storage import FileSystemStorage
from django.db import models
from jsonfield import JSONField



def key_generator(size=10, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


class BaseModel(models.Model):
    """
    Base model from which all other models should inherit. It has a unique key and other nice fields, like a unique id.
    If you override this class, you should probably add more unique identifiers, like a uuid or hash or something.
    """
    id = models.AutoField(primary_key=True)
    key = models.CharField(max_length=10, unique=True, db_index=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def generate_key(self, length=10):
        if not self.key:
            for _ in range(10):
                key = key_generator(length)
                if not type(self).objects.filter(key=key).count():
                    self.key = key
                    break

    def save(self, *args, **kwargs):
        self.generate_key()
        super(BaseModel, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class UserBackend(object):
    def authenticate(self, email=None, uuid=None):
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

    def get_user(self, user_id):
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

##########################################################################################


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

    def get_meetings(self, file):
        return {'meetings': {meeting.uuid: meeting.to_object(file) for meeting in self.meetings.all()}}

    def to_object(self, hub_uuid):
        """
        this should be things that are relatively constant, and won't need to be updated mid-meeting
        """

        return {'project_id': self.id,
                'key': self.key,
                'name': self.name,
                'badge_map': {member.badge: {"name": member.name, "key": member.key} for member in self.members.all()},
                'members': {member.name: member.to_object() for member in self.members.all()}
                }


class Hub(BaseModel):
    """Definition of a Hub, which is owned by a Project and has am externally generated uuid"""

    name = models.CharField(max_length=64)

    project = models.ForeignKey(Project, null=True, related_name="hubs")

    god = models.BooleanField(default=False)

    key = models.CharField(max_length=64, db_index=True, unique=True)
    """ng-device generated uuid"""

    def get_object(self, active_meeting = None):
        """
        These are all the things that change as the meeting progresses. Mainly the last_update for the hub.
        """
        if active_meeting:
            return {"name": self.name,
                    "last_update": active_meeting.last_log_index_for_hub(self),
                    "is_god": self.god}

        return {"name": self.name,
                "last_updates": {meeting.uuid: meeting.last_log_index_for_hub(self)
                                    for meeting in self.meetings.all()},
                "is_god": self.god}

    def __unicode__(self):
        return self.name


class Member(BaseModel):
    """Definition of a Member, who belongs to a Project, and owns a badge"""

    name = models.CharField(max_length=64)
    email = models.EmailField(unique=False, blank=True)
    badge = models.CharField(max_length=64)
    """Some sort of hub-readable ID for the badge, similar to a MAC, but accessible from iPhone"""

    project = models.ForeignKey(Project, related_name="members")

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
    """something like [project_name]|[random]|[start_time]"""

    metadata = models.OneToOneField(Event)
    """event data that will be continually updated with information about this meeting"""

    project = models.ForeignKey(Project, related_name="meetings")
    """The Project this Meeting belongs to"""

    def __unicode__(self):
        return unicode(self.project.name) + "|" + str(self.start_time)

    def get_events(self, hub = None):
        """get all events, optionally by hub"""
        if hub:
            return self.events.filter(hub=hub).latest()
        else:
            return self.events.all()

    def get_last_log_index_for_hub(self, hub):
        hubs_events = self.get_events(hub)

    def to_object(self, get_file = False):
        """Get an representation of this object for use with HTTP responses"""

        if get_file:
            return {"events": self.get_events(),
                    "metadata":self.metadata}

        return {"metadata": self.metadata}


class Event(models.Model):
    """
    Represents a piece of data uploaded by the phone. Could be anything from meeting starts to accelerometer data
    """

    type = models.CharField(max_length=64)
    """What kind of event this is: meeting start, audio recieve, etc"""

    log_timestamp = models.DecimalField(decimal_places=3, max_digits=20)
    """When the phone saved this log"""

    log_index = models.IntegerField()
    """Chronological ordering of the logs -- by hub!"""

    hub = models.ForeignKey(Hub, related_name="events")
    """Which hub recorded this event"""

    uuid = models.CharField(max_length=128, db_index=True)
    """Concatenation of project uuid, hub uuid, and log_index"""

    data = JSONField()
    """Whatever other data there is about this event"""

    meeting = models.ForeignKey(Meeting, related_name="events")
    """What meeting these are all a part of"""

    class Meta:
        order_by = 'log_timestamp'
        get_latest_by = 'log_index'



































































