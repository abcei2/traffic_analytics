from django.db import models
from django.contrib.postgres.fields import ArrayField
from core.model_utils import BaseModel
# Create your models here.



class VehicleAssessmentConfiguration(BaseModel):
    detection_roi=models.TextField(
        default='[  \
            {       \
                "y":0.4,\
                "x":0.4\
            },\
            {\
                "y":0.4,\
                "x":0.9\
            },\
            {\
                "y":0.9,\
                "x":0.9\
            },\
            {\
                "y":0.9,\
                "x":0.4\
            }\
        ]'
    )
    
class VehicleTypes(BaseModel):
    name = models.CharField(max_length=50, unique=True, null=False)

class VehicleAssessment(BaseModel):
    vehicle_type = models.ForeignKey(VehicleTypes, on_delete=models.CASCADE)

class StreetLanes(BaseModel):
    x_1=models.FloatField()
    y_1=models.FloatField()
    x_2=models.FloatField()
    y_2=models.FloatField()