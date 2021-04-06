from django.core.management.base import BaseCommand
from vehicle_counter.models import VehicleAssessmentConfiguration, VehicleTypes, StreetLanes

class Command(BaseCommand):
    help = 'Displays current time'

    def handle(self, *args, **kwargs):
        VehicleAssessmentConfiguration().save()

        VehicleTypes(name="Car").save()
        VehicleTypes(name="Biker").save()
        VehicleTypes(name="Truck").save()

        StreetLanes(x_1=0.2,y_1=0.2,x_2=0.8,y_2=0.8).save()