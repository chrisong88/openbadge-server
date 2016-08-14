import simplejson
from functools import wraps
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view
from .decorators import app_view, is_own_project
from .models import Meeting, Project, Hub, Event, Member
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

    init_data = simplejson.loads(request.data.get('meeting_init_data'))
    metadata = init_data['data']

    meeting = Meeting(version=metadata['log_version'],
                      project=request.hub.project,
                      uuid=metadata['uuid'])
    meeting.save()

    metadata['is_active'] = True
    metadata['hubs'] = {}
    metadata['members'] = {}
    metadata['start_time'] = init_data['log_timestamp']


    meeting_meta = Event(uuid=meeting.uuid + "|" + request.hub.uuid + "|" + "0",
                         type=init_data['type'],
                         log_index=init_data['log_index'],
                         log_timestamp=init_data['log_timestamp'],
                         hub=request.hub,
                         data=metadata,
                         meeting=meeting)
    meeting_meta.save()

    meeting.metadata = meeting_meta
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

    events = simplejson.loads(request.data.get('events'))
    # events = [simplejson.loads(event) for event in events]  # this is a bit strange... the actual chunk data posted
                                                              # is a json array of json strings of objects. So we have to
                                                              # first load the array, then each string

    if len(events) == 0:
        print "Received NO EVENTS from " + hub.name
        return JsonResponse({"status": "success", "data": hub.to_object()})

    if events[0]['log_index'] > meeting.get_last_log_index_for_hub(hub) + 1:
        return JsonResponse({"status": "missing events", "data": hub.to_object()})

    print "Received events ",
    for event in events:
        db_event = Event(uuid=meeting.uuid + "|" + hub.uuid + "|" + str(event['log_index']),
                         type=event['type'],
                         log_index=event['log_index'],
                         log_timestamp=event['log_timestamp'],
                         hub=hub,
                         data=event['data'],
                         meeting=meeting)
        db_event.save()
        print db_event.log_index,

        if db_event.type == "hub joined":
            metadata = meeting.metadata.data
            if (((hub.uuid in metadata['hubs'] and
                    metadata['hubs'][hub.uuid]['timestamp'] < db_event.log_timestamp)) or
                    hub.uuid not in metadata['hubs']):

                metadata['hubs'][hub.uuid] = {'active': True, 'timestamp':db_event.log_timestamp}
                meeting.metadata.save()

                hub.current_meeting = meeting
                hub.save()

        elif db_event.type == "hub left":
            metadata = meeting.metadata.data
            if ((hub.uuid in metadata['hubs'] and
                    metadata['hubs'][hub.uuid]['timestamp'] < db_event.log_timestamp) or
                    hub.uuid not in metadata['hubs']):

                metadata['hubs'][hub.uuid] = {'active': True, 'timestamp':db_event.log_timestamp}
                meeting.metadata.save()

                hub.current_meeting = None
                hub.save()

        elif db_event.type == "member joined":
            metadata = meeting.metadata.data
            member_key = db_event.data['key']
            if ((member_key in metadata['members'] and
                    metadata['members'][member_key]['timestamp'] < db_event.log_timestamp) or
                    member_key not in metadata['members']):

                metadata['members'][member_key] = {'active': True, 'timestamp':db_event.log_timestamp}
                meeting.metadata.save()

        elif db_event.type == "member left":
            metadata = meeting.metadata.data
            member_key = db_event.data['key']
            if ((member_key in metadata['members'] and
                    metadata['members'][member_key]['timestamp'] < db_event.log_timestamp) or
                    member_key not in metadata['members']):

                metadata['members'][member_key] = {'active': False, 'timestamp':db_event.log_timestamp}
                meeting.metadata.save()

        elif db_event.type == "meeting ended":
            metadata = meeting.metadata.data
            metadata['members']['is_active'] = False
            meeting.metadata.save()




    print " from " + hub.name

    return JsonResponse({"status": "success", "last_update_index": meeting.get_last_log_index_for_hub(hub)})


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
    project_name = request.META.get("HTTP_X_PROJECT_NAME")
    hub_name = request.META.get("HTTP_X_HUB_NAME")

    try:
        project = Project.objects.get(name=project_name)
    except Project.DoesNotExist:
        project = Project(name=project_name)
        project.save()

    try:
        hub = Hub(uuid=hub_uuid,
                  project=project,
                 name=hub_name)
        hub.save()
    except IntegrityError:
        hub = Hub.objects.get(uuid=hub_uuid)
        hub.name = hub_name
        hub.project = project
        hub.save()

    new_data = project.to_object(hub)

    return JsonResponse({"status": "added to project",
                         "project":new_data['project'],
                         'hub':new_data['hub']})


@is_own_project
@api_view(['GET'])
def get_hubs(request, project_key):
    try:
        request.hub = Hub.objects.get(uuid=request.META.get("HTTP_X_HUB_UUID"))
    except Hub.DoesNotExist:
        return HttpResponseNotFound()

    return JsonResponse(request.hub.to_object(float(request.META.get("HTTP_X_LAST_UPDATE"))))


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