from datetime import datetime, timedelta
from time import time
from pytz import timezone 
import pytz
import simplejson
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.widgets import AdminTextareaWidget
from django.contrib.auth import admin as auth_admin
from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html
from .models import OpenBadgeUser, Meeting, Member, Project, Hub


def register(model):
    def inner(admin_class):
        admin.site.register(model, admin_class)
        return admin_class

    return inner

class GetLocalTimeMixin(object):

    def get_local_time(self, timestamp):
        if timestamp == 0:
            return "(None)"
        else:
            return pytz.utc.localize(datetime.utcfromtimestamp(timestamp))\
                .astimezone(timezone(settings.TIME_ZONE))\
                .strftime('%Y-%m-%d %H:%M:%S %Z')

@register(OpenBadgeUser)
class OpenBadgeUserAdmin(auth_admin.UserAdmin):
    list_display = auth_admin.UserAdmin.list_display

    fieldsets = auth_admin.UserAdmin.fieldsets + (
        (_('OpenBadge User Data'), {'fields': ()}),
    )


class SerializedFieldWidget(AdminTextareaWidget):
    def render(self, name, value, attrs=None):
        return super(SerializedFieldWidget, self).render(name, simplejson.dumps(value, indent=4), attrs)


class MemberInline(admin.TabularInline, GetLocalTimeMixin):
    model = Member
    extra = 3
    warning_color = 'ff0000' #hexadecimal for the color of warning messages, currently bright red
    fields = ('key', 'name', 'email', 'badge', 
              'last_seen', 'voltage', 'last_audio', 'last_audio_ts',
              'last_audio_ts_fract', 'last_proximity_ts')
    readonly_fields = ('key', 'last_seen', 'last_audio', 'voltage')

    #if difference between now and last seen is more than 6 hours formats in color specified by warning_color
    def last_seen(self, obj):
        local_time = self.get_local_time(obj.last_seen_ts)
        if (time() - float(obj.last_seen_ts)) > 21600:

            return format_html(
                '<span style="color: #{};">{}</span>', # html formatting in the color specified by self.warning_color
                self.warning_color,
                local_time
            )
        else:
            return local_time

    def last_audio(self, obj):
        return self.get_local_time(obj.last_audio_ts)

    #if obj.last_voltage < 2.6, formats in color specified by warning_color
    def voltage(self, obj):
        if obj.last_voltage < 2.6:
            return format_html(
                '<span style="color : #{};">{}</span>',
                self.warning_color,
                obj.last_voltage
            )
        else:
            return obj.last_voltage

class MeetingInLine(admin.TabularInline, GetLocalTimeMixin):
    model = Meeting
    readonly_fields = ("uuid",)


class HubInline(admin.TabularInline, GetLocalTimeMixin):
    model = Hub

    fields = ("name", "god", "uuid", "last_seen", "last_hub_time", "time_difference_in_seconds", "ip_address", "key")
    readonly_fields = ("key", 'last_seen', "last_hub_time", "time_difference_in_seconds")

    def last_seen(self, obj):
        return self.get_local_time(obj.last_seen_ts)

    def last_hub_time(self, obj):
        return self.get_local_time(obj.last_hub_time_ts)

    def time_difference_in_seconds(self, obj):
        return abs(obj.last_seen_ts - obj.last_hub_time_ts)
        

@register(Project)
class ProjectAdmin(admin.ModelAdmin):
    readonly_fields = ("key",)
    list_display = ('name', 'key', 'id', 'number_of_members', 'number_of_meetings', 'total_meeting_time')
    list_filter = ('name',)
    inlines = (MemberInline, HubInline, MeetingInLine)
    actions_on_top = True

    def get_queryset(self, request):
        return Project.objects.prefetch_related("members", "hubs")

    # def members_list(self, inst):
    #     return ", ".join([member.name for member in inst.members.all()])
    # #members_list.admin_order_field = 'members_list'

    @staticmethod
    def number_of_members(inst):
        return len(inst.members.all())

    @staticmethod
    def number_of_meetings(inst):
        if inst.meetings.all():
            return len([meeting.uuid for meeting in inst.meetings.all()])
        return "NONE"

    # number_of_meetings.admin_order_field = 'number_of_meetings' #Allows column order sorting
    # number_of_meetings.short_description = 'Number of Meetings' #Renames column head

    @staticmethod
    def total_meeting_time(inst):
        if inst.meetings.all():
            def time_diff(x):
                if x.last_update_timestamp and x.start_time:
                    return (x.last_update_timestamp - x.start_time)
                return 0

            return timedelta(seconds = int(sum(
                [time_diff(meeting) for meeting in inst.meetings.all() if meeting.end_time])))
        return "NONE"


@register(Meeting)
class MeetingAdmin(admin.ModelAdmin, GetLocalTimeMixin):
    readonly_fields = ("key",)
    list_display = ('uuid', 'project_name', 'hub',
                    'start', 'end',
                    'last_update', 'last_update_index',
                    'duration',
                    'is_complete')
    actions_on_top = True


    def last_update(self, inst):
        if inst.last_update_timestamp:
            return self.get_local_time(inst.last_update_timestamp)

    def start(self, inst):
        if inst.start_time:
            return self.get_local_time(inst.start_time)

    def end(self, inst):
        if inst.end_time:
            return self.get_local_time(inst.end_time)


    def project_name(self, inst):
        return inst.project.name

    project_name.admin_order_field = 'project_name'
    project_name.short_description = 'Project'

    def duration(self, inst):
        return timedelta(seconds=int(inst.last_update_timestamp - inst.start_time))

    duration.admin_order_field = 'duration'
