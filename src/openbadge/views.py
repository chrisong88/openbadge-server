import simplejson
from functools import wraps
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view
from .decorators import app_view, is_own_project
from .models import Meeting, Project, Hub, Event


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
    if (request.method == 'GET'):
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
    hub = Hub.objects.get(uuid=request.headers.get("HTTP_X_HUB_UUID"))  # type: Hub


@api_view(['GET'])
def get_meeting(request, project_key):
    get_file = str(request.headers.get("HTTP_X_GET_FILE")).lower() == "true"

    if request.meeting:
        return request.meeting.to_object()

    return JsonResponse(request.hub.project.get_all_meetings(get_file))


@api_view(['POST'])
def post_meeting(request, project_key):
    meeting = request.meeting  # type: Meeting
    hub = request.hub # type: Hub
    events = simplejson.loads(request.data.get('chunks'))
    events = [simplejson.loads(event) for event in events]  # this is a bit strange... the actual chunk data posted
                                                            # is a json array of json strings of objects. So we have to
                                                            # first load the array, then each string

    if len(events) == 0:
        print "Received NO EVENTS from " + hub.name
        return JsonResponse({"status": "success", "data": hub.to_object()})

    if events[0]['log_index'] > hub.to_object()['last_update']['log_index'] + 1:
        return JsonResponse({"status": "missing events", "data": hub.to_object()})

    print "Received events ",
    for event in events:
        db_event = Event(uuid=meeting.uuid + "|" + hub.uuid + "|" + event['log_index'],
                         type=event['type'],
                         log_index=event['log_index'],
                         log_timestamp=event['log_timestamp'],
                         hub=hub,
                         data=event['data'],
                         meeting=meeting)
        db_event.save()
        print db_event.log_index,

    print " from " + hub.name

    return JsonResponse({"status": "success", "data": hub.to_object()})


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
    try:
        default_project = Project.objects.get(name="OB-DEFAULT")
    except Project.DoesNotExist:
        default_project = Project(name="OB-DEFAULT")
        default_project.save()

    hub = Hub(uuid=hub_uuid,
              project=default_project,
              name="New Hub")
    hub.save()
    return JsonResponse({"status": "added to default project"})


@is_own_project
@api_view(['GET'])
def get_hubs(request, project_key):
    return JsonResponse(request.hub.to_object())