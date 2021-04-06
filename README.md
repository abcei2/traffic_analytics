
# TRAFFIC ANALYTICS

A object counter app.

## BUILD
By the moment doesn't have full docker compose setup :(.  
git clone https://github.com/abcei2/traffic_analytics  
cd traffic_analytics  
**To setup rtmp server i use docker-compose**  
docker-compose up --build  
**Then**  
python traffic_analytics/manage.py makemigrations  && python traffic_analytics/manage.py migrate && python traffic_analytics/manage.py runserver  
**In other tab**  
python traffic_analytics/manage.py object_counter.py
**Open  http://localhost:8000/inicio**
