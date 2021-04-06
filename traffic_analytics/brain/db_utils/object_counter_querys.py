
from vehicle_counter.models import VehicleAssessment, VehicleTypes

def count_object(object_data):
    vehicle_type=VehicleTypes.objects.get(name=object_data["vehicle_type"])
    VehicleAssessment(vehicle_type=vehicle_type).save()