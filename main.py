from fastapi import FastAPI, Query, Path, Body, Request, HTTPException, UploadFile, File, Cookie, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Annotated, Optional, Union
from pydantic import BaseModel
from enum import Enum
import aiofiles

import pandas as pd
import pm4py
import pydotplus
from datetime import datetime, timedelta
import uuid, os
import base64

from fastapi.middleware.cors import CORSMiddleware

pd.set_option('display.max_columns', None)
SESSION_DURATION = timedelta(hours=2)
FILES_DIR = "files"
TEST_FILE="hardcoded/PurchasingExamplePseudo.csv"

# Remove old uploads at init
for filename in os.listdir(FILES_DIR):
    os.remove(f"{FILES_DIR}/{filename}")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], #["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_session_id(session_id: str = Cookie(None)):
    return session_id
    #return "fixed"

sessions = {}
app.mount("/static", StaticFiles(directory="static"), name="static")

from pm import (
    base64,
    units_per_role,
    role_average_duration,
    resource_average_duration,
    resource_roles,
    resource_role_average_duration,
    resource_within_role_normalization,
    roles_per_activity,
    resources_per_activity,
    activities_per_role,
    activity_average_duration_with_roles,
    activity_resource_comparison,
    activity_resource_role_comparison,
    slowest_resource_per_activity,
    calculate_working_days,
    capacity_utilization_resource,
    capacity_utilization_role,
    capacity_utilization_activity,
    activity_case_duration,
    total_duration_per_resource_and_activity,
    total_duration_per_role_and_activity,
    capacity_utilization_resource_new,
    workload_distribution_per_resource,
    capacity_utilization_role_new,
    capacity_utilization_activity_new,
    activities_per_role_new
    )

@app.get("/")
async def get_index():
    return FileResponse("static/index.html")

def process_file(file_location: str):
    df = pd.read_csv(file_location)
    # Convert "Start Time" and "Complete Time" columns to datatype: datetime
    df["Start Timestamp"] = pd.to_datetime(df["Start Timestamp"], format="%Y/%m/%d %H:%M:%S.%f")
    df["Complete Timestamp"] = pd.to_datetime(df["Complete Timestamp"], format="%Y/%m/%d %H:%M:%S.%f")
    # Calculate the time difference and create a new column
    df["Duration"] = df["Complete Timestamp"] - df["Start Timestamp"]
    df['Case ID'] = df['Case ID'].astype(str)
    return df

def describe_df(df):
    dff = df.drop(columns=["Duration"], inplace=False)
    dff = pm4py.format_dataframe(dff, case_id="Case ID", activity_key="Activity", timestamp_key="Complete Timestamp")
    event_log = pm4py.convert_to_event_log(dff)
    #heu_net = pm4py.discover_heuristics_net(event_log, dependency_threshold=0.99)
    heu_net = pm4py.discover_heuristics_net(dff, dependency_threshold=0.99, case_id_key='Case ID', activity_key='Activity', timestamp_key='Complete Timestamp')
    graph = pm4py.visualization.heuristics_net.visualizer.get_graph(heu_net)
    png_image = graph.create_png()
    image_base64 = base64.b64encode(png_image).decode('utf-8')
    stats = pm4py.statistics.traces.generic.log.case_statistics.get_cases_description(event_log)
    starts = [case['startTime'] for case in stats.values()]
    ends = [case['endTime'] for case in stats.values()]
    min_start = datetime.utcfromtimestamp(int(min(starts))).strftime("%d %b %Y")
    max_end = datetime.utcfromtimestamp(int(max(ends))).strftime("%d %b %Y")
    metrics = [
        {"Metric":"Cases", "Value":len(event_log)},
        {"Metric":"Events", "Value":sum(len(case) for case in event_log)},
        {"Metric":"Timeframe", "Value":f"{min_start} - {max_end}"}
    ]
    return (image_base64, metrics)

@app.post("/upload")
async def upload(file: UploadFile):
    session_id = str(uuid.uuid4())
    expiration_date = datetime.now() + SESSION_DURATION

    if not file:
        file = await aiofiles.open(TEST_FILE, mode='rb')

    file_location = f"{FILES_DIR}/{session_id}.csv"
    with open(file_location, "wb") as f:
        f.write(await file.read())
    if not isinstance(file, UploadFile):  #a fallback file
        await file.close()
    df = process_file(file_location)
    sessions[session_id] = {
        "file_location": file_location,
        "dataframe": df,
        "expiration": expiration_date
    }
    image_base64, metrics = describe_df(df)
    response = JSONResponse(content={"image":image_base64, "table":metrics})
    response.set_cookie(key="session_id", value=session_id)
    return response

@app.post("/fake_upload")
async def fake_upload(file: Optional[UploadFile] = File(None)):
    session_id = str(uuid.uuid4())
    expiration_date = datetime.now() + SESSION_DURATION

    file = await aiofiles.open(TEST_FILE, mode='rb')

    file_location = f"{FILES_DIR}/{session_id}.csv"
    with open(file_location, "wb") as f:
        f.write(await file.read())
    if not isinstance(file, UploadFile):  #a fallback file
        await file.close()
    df = process_file(file_location)
    sessions[session_id] = {
        "file_location": file_location,
        "dataframe": df,
        "expiration": expiration_date
    }
    image_base64, metrics = describe_df(df)
    response = JSONResponse(content={"image":image_base64, "table":metrics})
    response.set_cookie(key="session_id", value=session_id)
    return response


@app.middleware("http")
async def check_session(request: Request, call_next):
    current_session_id = request.cookies.get("session_id")
    if current_session_id:
        session = sessions.get(current_session_id)
        if session:
            print(f"Cookie: {current_session_id}\nExpiration: {session['expiration']}")
            if datetime.now() > session["expiration"]:
                # Cleanup
                os.remove(session["file_location"])
                del sessions[current_session_id]
                #raise HTTPException(status_code=401, detail="Session expired")
                response = JSONResponse(content={"detail":"Session expired"})
                response.status_code = 401
                return response
            else:
                # Extend session
                session["expiration"] = datetime.now() + SESSION_DURATION

    expired_sessions = [session_id for session_id, session in sessions.items() if datetime.now() > session["expiration"]]

    for session_id in expired_sessions:
        os.remove(sessions[session_id]["file_location"])
        del sessions[session_id]

    response = await call_next(request)
    if current_session_id and not session:
        response.delete_cookie(key="session_id")
    return response

@app.get("/test_expire")
async def test():
    raise HTTPException(status_code=401, detail="Session expired")


@app.get("/units")
async def read_units(session_id: str = Depends(get_session_id)):
    df = sessions[session_id]["dataframe"]
    return units_per_role(df)

@app.get("/duration_per_role")
async def read_units(session_id: str = Depends(get_session_id)):
    df = sessions[session_id]["dataframe"]
    return role_average_duration(df)

@app.get("/duration_per_resource")
async def read_units(session_id: str = Depends(get_session_id)):
    df = sessions[session_id]["dataframe"]
    return resource_average_duration(df)

@app.get("/resource_within_role_norm")
async def read_units(session_id: str = Depends(get_session_id)):
    df = sessions[session_id]["dataframe"]
    return resource_within_role_normalization(df)

@app.get("/resource_roles")
async def read_units(session_id: str = Depends(get_session_id)):
    df = sessions[session_id]["dataframe"]
    return resource_roles(df)

@app.get("/resource_role_duration")
async def read_units(session_id: str = Depends(get_session_id)):
    df = sessions[session_id]["dataframe"]
    return resource_role_average_duration(df)

@app.get("/roles_per_activity")
async def read_units(session_id: str = Depends(get_session_id)):
    df = sessions[session_id]["dataframe"]
    return roles_per_activity(df)

@app.get("/resources_per_activity")
async def read_units(session_id: str = Depends(get_session_id)):
    df = sessions[session_id]["dataframe"]
    return resources_per_activity(df)

@app.get("/activities_per_role")
async def read_units(session_id: str = Depends(get_session_id)):
    df = sessions[session_id]["dataframe"]
    return activities_per_role_new(df)

@app.get("/activity_average_duration")
async def read_units(session_id: str = Depends(get_session_id)):
    df = sessions[session_id]["dataframe"]
    return activity_average_duration_with_roles(df)

@app.get("/activity_resource_comparison")
async def read_units(session_id: str = Depends(get_session_id)):
    df = sessions[session_id]["dataframe"]
    return activity_resource_comparison(df)

@app.get("/activity_resource_comparison_norm")
async def read_units(session_id: str = Depends(get_session_id)):
    df = sessions[session_id]["dataframe"]
    return activity_resource_comparison(df, normalize=True)

@app.get("/activity_resource_role_comparison_norm")
async def read_units(session_id: str = Depends(get_session_id)):
    df = sessions[session_id]["dataframe"]
    return activity_resource_role_comparison(df, normalize=True)

@app.get("/slowest_resource")
async def read_units(session_id: str = Depends(get_session_id)):
    df = sessions[session_id]["dataframe"]
    return slowest_resource_per_activity(df)

@app.get("/capacity_utilization_resource")
async def read_units(session_id: str = Depends(get_session_id)):
    df = sessions[session_id]["dataframe"]
    return capacity_utilization_resource_new(df)

@app.get("/capacity_utilization_role")
async def read_units(session_id: str = Depends(get_session_id)):
    df = sessions[session_id]["dataframe"]
    return capacity_utilization_role_new(df)

@app.get("/capacity_utilization_activity")
async def read_units(session_id: str = Depends(get_session_id)):
    df = sessions[session_id]["dataframe"]
    return capacity_utilization_activity_new(df)

@app.get("/duration_per_activity")
async def read_units(session_id: str = Depends(get_session_id)):
    df = sessions[session_id]["dataframe"]
    return activity_case_duration(df)

@app.get("/resource_time_distribution")
async def read_units(session_id: str = Depends(get_session_id)):
    df = sessions[session_id]["dataframe"]
    return total_duration_per_resource_and_activity(df)

@app.get("/role_time_distribution")
async def read_units(session_id: str = Depends(get_session_id)):
    df = sessions[session_id]["dataframe"]
    return total_duration_per_role_and_activity(df)

@app.get("/resource_role_time_distribution")
async def read_units(session_id: str = Depends(get_session_id)):
    df = sessions[session_id]["dataframe"]
    return workload_distribution_per_resource(df)

