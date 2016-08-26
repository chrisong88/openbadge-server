import simplejson
from functools import wraps
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view
from .decorators import app_view, is_own_project
from .models import Meeting, Project, Hub, Event, Member, History
from django.db import IntegrityError

def json_response(**kwargs):
    return HttpResponse(simplejson.dumps(kwargs))


def context(**extra):
    return dict(**extra)


def render_to(template):
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            out = func(request, *args, **kwargs)
            if isinstance(out, dict):
                out = render(request, template, out)
            return out

        return wrapper

    return decorator


# Project Level Endpoints #

@app_view
@api_view(['GET'])
def projects(request):
    if request.method == 'GET':
        return get_project(request)
    return HttpResponseNotFound()


@api_view(['GET'])
def get_project(request):
    try:
        hub = Hub.objects.prefetch_related("project").get(uuid=request.META.get("HTTP_X_HUB_UUID"))
        return JsonResponse(hub.project.to_object(hub))
    except Hub.DoesNotExist:
        return HttpResponseNotFound()


# Meeting Level Endpoints #

@is_own_project
@app_view
@api_view(['PUT', 'GET', 'POST'])
def meetings(request, project_key):
    if request.method == 'PUT':
        return put_meeting(request, project_key)
    elif request.method == 'GET':
        return get_meeting(request, project_key)
    elif request.method == 'POST':
        return post_meeting(request, project_key)
    return HttpResponseNotFound()


@api_view(['PUT'])
def put_meeting(request, project_key):
    try:
        request.hub = Hub.objects.get(uuid=request.META.get("HTTP_X_HUB_UUID"))
    except Hub.DoesNotExist:
        return HttpResponseNotFound()

    log_version = request.META.get("HTTP_X_LOG_VERSION")
    meeting_uuid = request.META.get("HTTP_X_MEETING_UUID")

    meeting = Meeting(version=log_version,
                      project=request.hub.project,
                      uuid=meeting_uuid)

    meeting.save()

    request.hub.current_meeting = meeting
    request.hub.save()

    return JsonResponse({"status":"meeting created"})


@api_view(['GET'])
def get_meeting(request, project_key):
    try:
        request.hub = Hub.objects.get(uuid=request.META.get("HTTP_X_HUB_UUID"))
    except Hub.DoesNotExist:
        return HttpResponseNotFound()

    get_file = str(request.META.get("HTTP_X_GET_FILE")).lower() == "true"


    return JsonResponse(request.hub.project.get_all_meetings(get_file))


@api_view(['POST'])
def post_meeting(request, project_key):
    try:
        hub = Hub.objects.get(uuid=request.META.get("HTTP_X_HUB_UUID"))
        meeting = Meeting.objects.get(uuid=request.META.get("HTTP_X_MEETING_UUID"))
    except Hub.DoesNotExist:
        return HttpResponseNotFound()

    try:
        history = History.objects.get(hub=hub, meeting=meeting) # type:History
    except History.DoesNotExist:
        history = History(hub=hub, meeting=meeting) # type:History


    events = simplejson.loads(request.data['events'])
    # events = [simplejson.loads(event) for event in events]  # this is a bit strange... the actual chunk data posted
                                                              # is a json array of json strings of objects. So we have to
                                                              # first load the array, then each string


    if len(events) == 0:
        print "Received NO EVENTS from " + hub.name
        return JsonResponse({"status": "success", "last_update_index": history.last_log_index})

    if events[0]['log_index'] > history.last_log_index + 1:
        return JsonResponse({"status": "missing events", "last_update_index": history.last_log_index})

    print "Received events ",
    for event in events:

        try:
            db_event = Event.objects.get(hub=hub, meeting=meeting, log_index = event['log_index'])

        except Event.DoesNotExist:
            db_event = Event(type=event['type'],
                         log_index=event['log_index'],
                         log_timestamp=event['log_timestamp'],
                         hub=hub,
                         data=event['data'],
                         meeting=meeting)
            db_event.save()
        print db_event.log_index,

        if db_event.log_index > history.last_log_index:
            history.last_log_index = db_event.log_index
            history.save()

        if db_event.type == "meeting started":
            meeting.start_time = db_event.log_timestamp
            meeting.is_active = True
            meeting.save()


        elif db_event.type == "hub joined":
            hub.current_meeting = meeting
            hub.save()

            if not meeting.start_time:
                meeting.start_time = db_event.log_timestamp
                meeting.save()

            if history.last_activity_update < db_event.log_index:
                history.is_active = True
                history.last_activity_update = db_event.log_index
                history.save()



        elif db_event.type == "hub left":
            hub.current_meeting = None
            hub.save()

            if history.last_activity_update < db_event.log_index:
                history.is_active = False
                history.last_activity_update = db_event.log_index
                history.save()


        elif db_event.type == "member joined":
            member_key = db_event.data['key']

            print "Member joined!!!", member_key
            print member_key not in history.members

            if (member_key not in history.members
                    or history.members[member_key]['last_activity_update'] < db_event.log_index):
                history.members[member_key] = {'is_active': True, 'last_activity_update': db_event.log_index}

                history.save()



        elif db_event.type == "member left":
            member_key = db_event.data['key']

            if (member_key not in history.members
                    or history.members[member_key]['last_activity_update'] < db_event.log_index):

                history.members[member_key] = {'is_active': False, 'last_activity_update': db_event.log_index}

                history.save()

        elif db_event.type == "meeting ended":
                meeting.is_active = False
                meeting.end_time = float(db_event.log_timestamp)
                hub.current_meeting = None
                hub.save()




    print " from " + hub.name

    return JsonResponse({"status": "success", "last_update_index": history.last_log_index})


# Hub Level Endpoints #

@app_view
@api_view(['PUT', 'GET'])
def hubs(request, project_key):
    if request.method == 'PUT':
        return put_hubs(request, project_key)
    elif request.method == 'GET':
        return get_hubs(request, project_key)
    return HttpResponseNotFound()


@api_view(['PUT'])
def put_hubs(request, project_key):
    hub_uuid = request.META.get("HTTP_X_HUB_UUID")
    hub_name = request.META.get("HTTP_X_HUB_NAME")
    try:
        # First try to access the default project, creating it if it doesnt exist already
        project = Project.objects.get(name='OB-DEFAULT')
    except Project.DoesNotExist:
        project = Project(name='OB-DEFAULT')
        project.save()

    try:
        # Then try to add this hub to that project. if this fails, its probably because th hub already exists.
        hub = Hub(uuid=hub_uuid,
                  project=project,
                  name=hub_name)
        hub.save()
        return JsonResponse({"status": "added hub to default project"})
    except IntegrityError:
        # If that hub already exists, just rename it.
        hub = Hub.objects.get(uuid=hub_uuid)
        hub.name = hub_name
        hub.save()
        return JsonResponse({"status": "renamed hub"})


@is_own_project
@api_view(['GET'])
def get_hubs(request, project_key):
    try:
        request.hub = Hub.objects.get(uuid=request.META.get("HTTP_X_HUB_UUID"))
    except Hub.DoesNotExist:
        return HttpResponseNotFound()

    last_update = float(request.META.get("HTTP_X_LAST_UPDATE"))
    return JsonResponse(request.hub.to_object(last_update))


@is_own_project
@api_view(['PUT'])
def put_members(request, project_key):
    try:
        request.hub = Hub.objects.get(uuid = request.META.get("HTTP_X_HUB_UUID"))
    except Hub.DoesNotExist:
        return HttpResponseNotFound()

    try:
        member = Member.objects.filter(project = request.hub.project).get(badge= request.META.get("HTTP_X_BADGE_UUID"))
        member.name = request.META.get("HTTP_X_MEMBER_NAME")

    except Member.DoesNotExist:
        member = Member(name=request.META.get("HTTP_X_MEMBER_NAME"),
                        badge=request.META.get("HTTP_X_BADGE_UUID"),
                        project=request.hub.project)

    member.save()
    return JsonResponse({"status":"added to project"})