from django.core.management.base import BaseCommand
from django.db import IntegrityError
from vehicle_counter.models import VehicleAssessmentConfiguration, VehicleTypes, StreetLanes

class Command(BaseCommand):
    help = 'Displays current time'

    def handle(self, *args, **kwargs):
        try:
            VehicleTypes(name="Car").save()
            VehicleTypes(name="Person").save()
            VehicleTypes(name="Motorbike").save()
            VehicleTypes(name="Bus").save()
            VehicleTypes(name="Bike").save()
            VehicleAssessmentConfiguration().save()
            StreetLanes(x_1=0.2,y_1=0.2,x_2=0.8,y_2=0.8).save() 

            print("DATA LOADED")
        except IntegrityError:
            print("DATA ALREADY LOADED")
        