# REOSURCE ANALYTICS TOOL

The following **Resource Analytics Tool** is a web-based application for analyzing resource-related insights from event logs. It visualizes metrics from four critical areas: resource allocation, resource performance, workload distribution, and capacity utilization using interactive plots and tables.

---

## Project Structure
```
.
├── main.py # FastAPI backend with endpoints
├── unlock.py # Optional pre-processing script for custom logs
├── pm.py # Process mining logic
├── run.sh # Entrypoint script for Docker and API setup
├── Dockerfile # Docker build file
├── requirements.txt # Python dependencies
├── deployment.yaml # Kubernetes deployment config
├── hardcoded # event logs
│ ├── Purchasing example.csv
│ ├── Purchasing example.csv
├── static/
│ ├── index.html # Frontend HTML
│ ├── style.css # Styling
│ ├── script.js # Frontend behavior
└── ...
```
---

## :rocket: Features
- Upload event logs (CSV)
- Perform interactive visual analytics:
    - Resource allocation
    - Case duration statistics
    - Workload distribution
    - Capacity utilization
- Process model visualization
- Responsive web UI using HTML/CSS/JavaScript

---

## :whale: Docker Usage

1. Build the container: `docker build -t resource-analytics .`
4. Run the container: `docker run -p 9090:9090 -ti resource-analytics`
5. Access the interface: open your browser and navigate to: http://localhost:9090

---

## Input Requirements
Input logs **must be in CSV format** and include the following columns:

| Column              | Description                     |
|:--------------------|:--------------------------------|
| `Case ID`           | Unique identifier per process   |
| `Start Timestamp`   | Activity start time             |
| `Complete Timestamp`| Activity end time               |
| `Activity`          | Activity name                   |
| `Resource`          | Human resource identifier       |
| `Role`              | Role of the resource            |

---

## Upload Logs
The upload section allows you to load an event log. A default log (PurchasingExample) is used if no file is selected.

To use your own event log:
1. Uncomment the line '''#RUN python3 unlock.py''' in the Dockerfile.
2. Rebuild and re-run the container.

## Analyses Types & Descriptions
After upload, choose from multiple analysis options in the dropdown. Categories include:

#### Resource Allocation

| **Analysis**               | **Description** |
|:---------------------------|:----------------|
| **Unique Resources**       | Counts the number of distinct resources involved in the event log. |
| **Roles per Resource**     | Displays how many roles each resource has taken on. |
| **Resources per Activity** | Shows how many different resources performed each activity. |
| **Activities per Role**    | Summarizes which and how many activities are carried out by each role. |

---

#### Case Duration

| **Analysis**                                      | **Description** |
|:--------------------------------------------------|:----------------|
| **Duration per Role**                             | Average duration of cases broken down by the role of the executing resource. |
| **Duration per Role and Resource**                | Average duration per case for each combination of role and resource. |
| **Duration per Activity**                         | Shows how long each activity takes on average. |
| **Duration per Activity and Role (Heatmap)**      | Visual heatmap of average durations for each activity-role pair. |
| **Duration per Activity and Resource**            | Displays average time per activity for each resource. |
| **Duration per Activity and Resource (Heatmap)**  | Heatmap showing activity durations by resource. |
| **Duration per Activity and Resource by Role (Heatmap)** | Triple-dimension heatmap showing how role affects activity durations across resources. |

---

#### Workload Distribution

| **Analysis**            | **Description** |
|:-------------------------|:----------------|
| **Role by Resource**     | Number of events handled by each role-resource combination over time. |
| **Activity by Resource** | How workload is distributed across resources for each activity. |
| **Activity by Role**     | Similar to above, but aggregated by role instead of resource. |

---

#### Capacity Utilization

| **Analysis**                      | **Description** |
|:----------------------------------|:----------------|
| **Resource Capacity Utilization** | Utilization rates of each individual resource based on activity timing. |
| **Role Capacity Utilization**     | Aggregated utilization of roles across the organization. |
| **Activity Capacity Utilization** | Identifies activities with the most resource load relative to availability. |


Each option triggers a backend API to generate plots and tables using Plotly and Tabulator.


