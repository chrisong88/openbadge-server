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
        return {
            'project': {
                'key': self.key,
                'name': self.name,
                'members': {member.badge: {"name": member.name, "key": member.key}
                            for member in self.members.all()},
                'active_meetings': [meeting.to_object()
                                        for meeting in self.meetings.filter(is_active=True)
                                    ]},
            'hub': {
                "name": hub.name,
                "last_updates": {history.meeting.uuid: history.last_log_index
                                    for history in hub.histories.all()
                                 },
                "su": hub.su,
                'meeting': hub.current_meeting.to_object() if hub.current_meeting else None
            }
        }


class Hub(BaseModel):
    """Definition of a Hub, which is owned by a Project and has an externally generated uuid"""

    name = models.CharField(max_length=64)

    project = models.ForeignKey(Project, null=True, related_name="hubs", on_delete=models.CASCADE)

    current_meeting = models.ForeignKey('Meeting', null=True, blank=True, related_name="hubs", on_delete=models.SET_NULL)

    su = models.BooleanField(default=False)
    """Is this a Super User? Gets updated mid-meeting."""

    uuid = models.CharField(max_length=64, db_index=True, unique=True)
    """ng-device generated uuid"""

    def to_object(self, last_update=0):
        return {"badge_map":{member.badge: {"name": member.name, "key": member.key}
                             for member in self.project.members.all()
                             if int(member.date_updated.strftime("%s")) > last_update},
                "meeting":self.current_meeting.get_meta(self) if self.current_meeting else None,
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
        return {'key':self.key, 'name':self.name, 'badge':self.badge}

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
    """something like [project_key]|[start_time], start time in ms, making it infeasible to `hack`"""

    is_active = models.BooleanField(default=False)
    """If there are still hubs present --- effectively: `end_time === None`"""

    start_time = models.DecimalField(decimal_places=3, max_digits=20, null=True, blank=True)
    """When the first hub joins"""

    end_time = models.DecimalField(decimal_places=3, max_digits=20, null=True, blank=True)
    """When the last hub leaves"""

    project = models.ForeignKey(Project, related_name="meetings", on_delete=models.CASCADE)
    """The Project this Meeting belongs to"""

    def duration(self):
        if self.end_time:
            timedelta(seconds=int(self.end_time - self.start_time))
        return timedelta(seconds=int(self.events.latest().log_timestamp- self.start_time))


    def __unicode__(self):
        return unicode(self.project.key) + " | " + str(self.start_time)


    def get_meta(self, hub=None):
        if hub:
            return {
                'start_time': self.start_time,
                'end_time': self.end_time if self.end_time else None,
                'history': History.objects.get(meeting=self, hub=hub).to_object()
                            if History.objects.filter(meeting=self, hub=hub).exists()
                            else None
            }
        return {
                'start_time': self.start_time,
                'end_time': self.end_time if self.end_time else None,
                'history': { hub_history.hub.uuid: History.objects.get(meeting=self, hub=hub_history.hub).to_object()
                                        for hub_history in History.objects.filter(meeting=self) }
            }

    def get_events(self, hub = None):
        """get all events, optionally by hub"""
        if hub:
            return self.events.filter(hub=hub)
        else:
            return self.events.all()

    def to_object(self, get_file = False):
        """Get an representation of this object for use with HTTP responses"""

        if get_file:
            return {"events": [event.to_object() for event in self.get_events()],
                    "metadata":self.get_meta()}

        return {"metadata": self.get_meta()}


class History(models.Model):

    is_active = models.BooleanField(default=False)

    last_activity_update = models.IntegerField(default=-1)

    last_log_index = models.IntegerField(default=-1)

    members = JSONField(null=True, blank=True, default={})
    """JSON associated array of active member address's to {timestamp when we last heard from them, is_active}"""

    hub = models.ForeignKey('Hub', related_name="histories", null=True, on_delete=models.SET_NULL)
    meeting = models.ForeignKey('Meeting', related_name="histories", null=True, on_delete=models.CASCADE)

    def to_object(self):

        return {
            'is_hub_active': self.is_active,
            'last_log_index': self.last_log_index,
            'active_members': [
                address for address, status in self.members.iteritems() if status['is_active']
            ]
        }
        pass

    class Meta:
        index_together = ['meeting', 'hub']
        verbose_name_plural = "histories"


class Event(models.Model):
    """
    Represents a piece of data uploaded by the phone. Could be anything from meeting starts to accelerometer data
    """

    id = models.AutoField(primary_key=True)
    """Some sort of index thing"""

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

    def __unicode__(self):
        return self.type + " recorded by " + self.hub.uuid + " at " + str(float(self.log_timestamp))

    class Meta:
        unique_together = (('log_index', 'hub', 'meeting'),)
        index_together = [['log_index', 'hub', 'meeting']]
        ordering = ['log_timestamp']
        get_latest_by = 'log_index'