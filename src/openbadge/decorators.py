from functools import wraps
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound
from .models import Meeting, Hub


def is_own_project(f):
    """ensures a hub that accesses a given /:projectID/whatever is a member of the project with that ID"""

    @wraps(f)
    def wrap(request, project_key, *args, **kwargs):


        hub_uuid = request.META.get("HTTP_X_HUB_UUID")
        try:
            hub = Hub.objects.prefetch_related("project").get(uuid=hub_uuid)
        except Hub.DoesNotExist:
            return HttpResponseNotFound()
        hub_project_key = hub.project.key
        if str(hub_project_key) == str(project_key):
            return f(request, project_key, *args, **kwargs)

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