from functools import wraps
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound
from .models import Meeting, Hub


class SimpleRequest:
    def __init__(self, request, hub, meeting):
        self.meeting = meeting
        self.method = request.method
        self.hub = hub
        self.headers = request.META
        self.data = request.data


def is_own_project(f):
    """ensures a hub that accesses a given /:projectKey/whatever is a member of the project with that Key"""

    @wraps(f)
    def wrap(request, project_key, *args, **kwargs):

        try:
            hub = Hub.objects.prefetch_related("project").get(uuid=request.META.get("HTTP_X_HUB_UUID"))
        except Hub.DoesNotExist:
            return HttpResponseNotFound()

        try:
            meeting = Meeting.objects.get(uuid=request.META.get("HTTP_X_MEETING_UUID"))
        except Meeting.DoesNotExist:
            meeting = None

        if str(hub.project.key) == str(project_key):
            return f(SimpleRequest(request, hub, meeting), project_key, *args, **kwargs)

        class HttpResponseUnauthorized(HttpResponse):
            status_code = 401

        return HttpResponseUnauthorized()

    return wrap


def app_view(f):
    """ensures a valid X-APPKEY has been set in a request's header"""

    @wraps(f)
    def wrap(request, *args, **kwargs):
        token = request.META.get("HTTP_X_APPKEY")
        if token != settings.APP_KEY:
            return HttpResponseBadRequest()

        return f(request, *args, **kwargs)

    return wrap