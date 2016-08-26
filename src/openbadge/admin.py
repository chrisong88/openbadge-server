from datetime import datetime, timedelta
from pytz import timezone
import pytz
import simplejson
from django.contrib import admin
from django.contrib.admin.widgets import AdminTextareaWidget
from django.contrib.auth import admin as auth_admin
from django.utils.translation import ugettext_lazy as _
from .models import OpenBadgeUser, Meeting, Member, Project, Hub, Event, CurrentState


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


    def active_members(self, inst):
        active_members = []
        for current_state in inst.current_states.all():
            active_members += current_state.to_object()['active_members']
        return ', '.join(active_members)

    def active_hubs(self, inst):
        return simplejson.dumps([{current_state.hub.uuid: current_state.last_log_index}
                          for current_state in inst.current_states.all()
                          if current_state.is_active])




class HubInline(admin.TabularInline):
    model = Hub
    readonly_fields = ("key",)


class EventInline(admin.TabularInline):
    model = Event
    extra = 0

class CurrentStateInline(admin.TabularInline):
    model = CurrentState
    extra = 0

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
    readonly_fields = ("key",'is_active','active_members','active_hubs','start_time','end_time')
    list_display = ('uuid', 'project','is_active','active_members','active_hubs',
                    'duration','start_time','end_time')
    actions_on_top = True

    inlines = (EventInline, CurrentStateInline)

    eastern = timezone("US/Eastern")

    def get_local_time(self, timestamp):
        try:
            return pytz.utc.localize(datetime.utcfromtimestamp(timestamp))\
                .astimezone(self.eastern)\
                .strftime('%Y-%m-%d %H:%M:%S %Z%z')
        except TypeError:
            return None

    @staticmethod
    def metadata_string(inst):
        return inst.metadata.data


    def active_members(self, inst):
        active_members = []
        for current_state in inst.current_states.all():
            active_members += current_state.to_object()['active_members']
        return ', '.join(active_members)

    def active_hubs(self, inst):
        return simplejson.dumps([{current_state.hub.uuid: current_state.last_log_index}
                          for current_state in inst.current_states.all()
                          if current_state.is_active])

