
from core.view_utils import BaseView, sanitize_html
from django.shortcuts import redirect, render, get_object_or_404
from vehicle_counter.models import VehicleAssessmentConfiguration, VehicleTypes, StreetLanes
from django.http import JsonResponse
import json
import uuid
# Create your views here.
class Home(BaseView):
    template = "vehicle_counter/home.html"
    # custom_stylesheet = "journal.min.css"

    def get(self, request, *args, **kwargs):
      
        detection_roi=VehicleAssessmentConfiguration.objects.all().values()[0]["detection_roi"]
        vehicle_types=list(VehicleTypes.objects.all().values('id','name','enabled'))
        street_lanes=list(StreetLanes.objects.all().values('id','x_1','y_1','x_2','y_2'))

        for i in range(len(street_lanes)):
            street_lanes[i]["id"]=str(street_lanes[i]["id"])
        for i in range(len(vehicle_types)):
            vehicle_types[i]["id"]=str(vehicle_types[i]["id"])

        context = {
            "detection_roi":detection_roi,      
            "street_lanes":street_lanes,
            "vehicle_types":vehicle_types,
            "title": "TRAFFIC",
        }
        return self.render_template(request, context)

    def post(self, request, *args, **kwargs):
        return redirect("vehicle_counter:vehicle_counter")
        
def update_roi(request):
    if request.method == "POST":
        detection_roi = request.POST.get("detection_roi")
        vehi_confi=VehicleAssessmentConfiguration.objects.all()[0]
        vehi_confi.detection_roi=detection_roi
        vehi_confi.save()
        return JsonResponse({"ok":"OK"})

def update_lane_separator(request):
    if request.method == "POST":
        lanes_separator = json.loads(request.POST.get("lanes_separator"))
        for i in range(len(lanes_separator)):
            StreetLanes.objects.filter(id=uuid.UUID(lanes_separator[i]["id"]).hex).update(                
                x_1=lanes_separator[i]["x_1"],
                y_1=lanes_separator[i]["y_1"],
                x_2=lanes_separator[i]["x_2"],
                y_2=lanes_separator[i]["y_2"]
            )
        return JsonResponse({"ok":"OK"})

def update_enabled_types(request):    
    if request.method == "POST":
        id_checked = json.loads(request.POST.get("id_checked"))
        enabled = json.loads(request.POST.get("enabled"))
        print(enabled)
        # VehicleTypes.objects.filter(id=uuid.UUID(id_checked).hex).update(                
        #     enabled=lanes_separator[i]["x_1"]   
        # )
        return JsonResponse({"ok":"OK"})