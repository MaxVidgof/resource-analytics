# Resource analytics

## Usage (with Docker)
1. Build the container:
  ```docker build -t resource-analytics .```
2. Run the container:
  ```docker run -p 9090:9090 -ti resource-analytics```
3. You can now replicate the experiment with the provided event log.

If you want to use your own event logs, uncomment the line ```#RUN python3 unlock.py``` in the ```Dockerfile``` and repeat steps 1-2. 
Keep in mind that the tool only accepts event logs in the CSV format and assumes the presence of at least the following columns:
Case ID, Start Timestamp, Complete Timestamp, Activity, Resource, Role
