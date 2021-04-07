from brain.db_utils.object_counter_querys import count_object
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Excecute counter!!!'

        
    def handle(self, *args, **kwargs):
        object_data={
            "vehicle_type":"Car2"
        }
        count_object(object_data)
        
        

