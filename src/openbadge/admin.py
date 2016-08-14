from datetime import datetime, timedelta
from pytz import timezone
import pytz
import simplejson
from django.contrib import admin
from django.contrib.admin.widgets import AdminTextareaWidget
from django.contrib.auth import admin as auth_admin
from django.utils.translation import ugettext_lazy as _
from .models import OpenBadgeUser, Meeting, Member, Project, Hub


def register(model):
    def inner(admin_class):
        admin.site.register(model, admin_class)
        return admin_class

    return inner


@register(OpenBadgeUser)
class OpenBadgeUserAdmin(auth_admin.UserAdmin):
    list_display = auth_admin.UserAdmin.list_display

    fieldsets = auth_admin.UserAdmin.fieldsets + (
        (_('OpenBadge User Data'), {'fields': ()}),
    )


class SerializedFieldWidget(AdminTextareaWidget):
    def render(self, name, value, attrs=None):
        return super(SerializedFieldWidget, self).render(name, simplejson.dumps(value, indent=4), attrs)


class MemberInline(admin.TabularInline):
    model = Member
    readonly_fields = ("key",)
    extra = 3


class MeetingInLine(admin.TabularInline):
    model = Meeting
    extra = 0
    readonly_fields = ('key',"uuid",'is_active','active_members','active_hubs')
    fields = ('key','uuid','is_active','active_members','active_hubs')


    def is_active(self, inst):
        return inst.metadata.data['is_active']
    def active_members(self, inst):
        #return inst.metadata.data['members']
        return ', '.join([member for member,data in inst.metadata.data['members'].iteritems() if data['active']])
    def active_hubs(self, inst):
        #return inst.metadata.data['hubs']
        return ', '.join([hub for hub,data in inst.metadata.data['hubs'].iteritems() if data['active']])



class HubInline(admin.TabularInline):
    model = Hub
    readonly_fields = ("key",)


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
        return inst.members.count()

    @staticmethod
    def number_of_meetings(inst):
        return inst.meetings.count()

    # number_of_meetings.admin_order_field = 'number_of_meetings' #Allows column order sorting
    # number_of_meetings.short_description = 'Number of Meetings' #Renames column head

    @staticmethod
    def total_meeting_time(inst):
        if inst.meetings.all():
            return timedelta(seconds =
                int(sum([meeting.duration().total_seconds() for meeting in inst.meetings.all()])))
        return timedelta(seconds=0)


@register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    readonly_fields = ("key",'is_active','active_members','active_hubs',)
    list_display = ('uuid', 'project',
                    'is_active','active_members','active_hubs',
                    'duration')
    actions_on_top = True

    eastern = timezone("US/Eastern")

    def get_local_time(self, timestamp):
        return pytz.utc.localize(datetime.utcfromtimestamp(timestamp))\
            .astimezone(self.eastern)\
            .strftime('%Y-%m-%d %H:%M:%S %Z%z')

    def last_update(self, inst):
        if inst.last_update_timestamp:
            return self.get_local_time(inst.events.latest().log_timestamp)

    def start(self, inst):
        return self.get_local_time(inst.get_meta('start_time'))

    def end(self, inst):
        if inst.end_time:
            return self.get_local_time(inst.events.latest().log_timestamp)

    @staticmethod
    def metadata_string(inst):
        return inst.metadata.data


    def is_active(self, inst):
        return inst.metadata.data['is_active']
    def active_members(self, inst):
        #return inst.metadata.data['members']
        return ', '.join([member for member,data in inst.metadata.data['members'].iteritems() if data['active']])
    def active_hubs(self, inst):
        #return inst.metadata.data['hubs']
        return ', '.join([hub for hub,data in inst.metadata.data['hubs'].iteritems() if data['active']])
