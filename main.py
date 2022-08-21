import os
import gpxpy
import pandas as pd
import json
import datetime
import matplotlib.pyplot as plt

columns_of_interest = {
    "com.samsung.health.exercise.duration": "Duration",
    "com.samsung.health.exercise.location_data": "LocationData",
    "com.samsung.health.exercise.start_time": "StartTime",
    "com.samsung.health.exercise.max_altitude": "MaxAltitude",
    "com.samsung.health.exercise.min_altitude": "MinAltitude",
    "com.samsung.health.exercise.update_time": "UpdateTime",
    "com.samsung.health.exercise.create_time": "CreateTime",
    "com.samsung.health.exercise.max_speed": "MaxSpeed",
    "com.samsung.health.exercise.distance": "Distance",
    "com.samsung.health.exercise.mean_speed": "MeanSpeed",
    "com.samsung.health.exercise.end_time": "EndTime",
    "com.samsung.health.exercise.datauuid": "DataUUID"
}

data_folder = "data"
adidas_run_gpx_folder = f"{data_folder}/export-20220527-000/Sport-sessions/GPS-data"
samsung_health_folder = f"{data_folder}/samsunghealth_hakan.karakus.007_202208210946"
samsung_health_csv_file = f"{samsung_health_folder}/com.samsung.shealth.exercise.202208210946.csv"
samsung_health_json_folder = f"{samsung_health_folder}/jsons/com.samsung.shealth.exercise"

def date_to_str(date):
    y = str(date.year).zfill(4)
    m = str(date.month).zfill(2)
    d = str(date.day).zfill(2)
    h = str(date.hour).zfill(2)
    n = str(date.minute).zfill(2)
    s = str(date.second).zfill(2)
    a = f"{y}{m}{d}_{h}{n}{s}"
    return a

def json_to_gpx(json_file):
    c = json_file[0]
    points = []
    with open(f"{samsung_health_json_folder}/{c}/{json_file}", "r+") as file:
        for point in json.load(file):
            p = gpxpy.gpx.GPXTrackPoint(latitude=point["latitude"],
                                        longitude=point["longitude"],
                                        elevation=point["altitude"],
                                        time=datetime.datetime.fromtimestamp(point["start_time"] / 1000))
            points.append(p)
    x = gpxpy.gpx.GPX()
    s = gpxpy.gpx.GPXTrackSegment(points)
    t = gpxpy.gpx.GPXTrack()
    t.segments = [s]
    x.tracks = [t]
    x.time = points[0].time
    file_name = date_to_str(points[0].time)
    return x, file_name

def fix_gpx(gpx):
    gpx.adjust_time(datetime.timedelta(hours=3), all=True)
    gpx.link = None
    gpx.name = None
    gpx.description = None
    gpx.copyright_author = None
    gpx.copyright_license = None
    gpx.copyright_year = None
    gpx.creator = None
    gpx.tracks[0].name = None
    gpx.tracks[0].link = None
    date = gpx.time
    file_name = date_to_str(date)
    return gpx, file_name

def create_gpx_adidas_run():
    for gpx_file_name in os.listdir(f"{adidas_run_gpx_folder}"):
        with open(f"{adidas_run_gpx_folder}/{gpx_file_name}", "r+") as gpx_file:
            gpx, file_name = fix_gpx(gpxpy.parse(gpx_file))
            with open(f"gpx/{file_name}.gpx", "w+") as file:
                file.write(gpx.to_xml())

def create_gpx_samsung_health():
    df = pd.read_csv(samsung_health_csv_file, skiprows=1, index_col=False)
    # 11007 is the id of bicycle activity
    df = df[df["com.samsung.health.exercise.exercise_type"] == 11007]
    df = df[columns_of_interest.keys()]
    df = df.rename(columns=columns_of_interest)
    df = df.reset_index()
    for json_file in df["LocationData"]:
        gpx, file_name = json_to_gpx(json_file)
        with open(f"gpx/{file_name}.gpx", "w+") as file:
            file.write(gpx.to_xml())

def create_gpx():
    if not os.path.exists("gpx"):
        os.mkdir("gpx")
    create_gpx_adidas_run()
    create_gpx_samsung_health()

def gpx_to_df(gpx_file_name):
    with open(gpx_file_name, "r+") as gpx_file:
        gpx = gpxpy.parse(gpx_file)
        points = gpx.tracks[0].segments[0].points
    lst = []
    for p in points:
        dct = {
            "Time": p.time,
            "Latitude": p.latitude,
            "Longitude": p.longitude,
            "Elevation": p.elevation
        }
        lst.append(dct)
    return pd.DataFrame(lst)

def plot_all(png_file_name, name="Bicycle Routes"):
    fig, ax = plt.subplots()
    a_mins = []
    a_maxs = []
    b_mins = []
    b_maxs = []
    for g in os.listdir("gpx"):
        df = gpx_to_df(f"gpx/{g}")
        a = df["Longitude"]
        b = df["Latitude"]
        if a.min() > 30:
            a_mins.append(a.min())
            a_maxs.append(a.max())
            b_mins.append(b.min())
            b_maxs.append(b.max())
            ax.plot(a, b, lw=1, color="#0000ff")
    ax.axis("square")
    a_min = min(a_mins)
    a_max = max(a_maxs)
    b_min = min(b_mins)
    b_max = max(b_maxs)
    a_off = (a_max - a_min) * 0.1
    b_off = (b_max - b_min) * 0.1
    x_min, x_max = round(a_min - a_off, 2), round(a_max + a_off, 2)
    y_min, y_max = round(b_min - b_off, 2), round(b_max + b_off, 2)
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(name)
    print(x_min, x_max, y_min, y_max)
    plt.savefig(f"{png_file_name}.png", dpi=600)

def plot(file_name, a, b, name="Bicycle Route", color="#0000FF"):
    fig, ax = plt.subplots()
    ax.plot(a, b, lw=1, color=color)
    ax.axis("square")
    a_min, a_max = a.min(), a.max()
    b_min, b_max = b.min(), b.max()
    a_off = (a_max - a_min) * 0.1
    b_off = (b_max - b_min) * 0.1
    ax.set_xlim(a_min - a_off, a_max + a_off)
    ax.set_ylim(b_min - b_off, b_max + b_off)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(name)
    plt.savefig(f"{file_name}.png", dpi=600)


def plot_gpx(gpx_file_name, png_file_name="test"):
    df = gpx_to_df(gpx_file_name)
    plot(png_file_name, df["Longitude"], df["Latitude"])

if __name__ == "__main__":
    create_gpx()
