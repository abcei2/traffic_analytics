
from vehicle_counter.models import VehicleAssessment, VehicleTypes
from django.core.exceptions import ObjectDoesNotExist

def count_object(object_data):

    try:        
        vehicle_type=VehicleTypes.objects.get(name=object_data["vehicle_type"])
        VehicleAssessment(vehicle_type=vehicle_type).save()
        print("Saved object: ",object_data)
        return True
    except ObjectDoesNotExist:
        pass
    except:
        print("Some other error ocurr")
    return False
    #VehicleAssessment(vehicle_type=vehicle_type).save()