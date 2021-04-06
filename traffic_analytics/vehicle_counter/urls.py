from django.urls import path
from django.conf.urls import url
from django.http import StreamingHttpResponse

from camera import VideoCamera, gen
from vehicle_counter.views import update_roi, update_lane_separator

app_name = "vehicle_counter"
urlpatterns = [
    path('monitor/', lambda r: StreamingHttpResponse(gen(VideoCamera()),
                                                     content_type='multipart/x-mixed-replace; boundary=frame'),name="monitor"),

    path("update_roi", update_roi, name="update_roi"),

    path("update_lane_separator", update_lane_separator, name="update_lane_separator"),
]

