import gpxpy
import gpxpy.gpx
import datetime
import geopy.distance

# Function to calculate the distance between two points
def calculate_distance(lat1, lon1, lat2, lon2):
    coords_1 = (lat1, lon1)
    coords_2 = (lat2, lon2)
    return geopy.distance.distance(coords_1, coords_2).meters

# Function to interpolate time between two points
def interpolate_time(start_time, end_time, start_index, end_index, index):
    total_points = end_index - start_index
    time_difference = end_time - start_time
    interpolated_time = start_time + (time_difference / total_points) * (index - start_index)
    return interpolated_time

# Load and parse the GPX file
def load_gpx(file_path):
    with open(file_path, 'r') as file:
        gpx = gpxpy.parse(file)
    return gpx

# Save the cleaned GPX data to a new file
def save_gpx(gpx, file_path):
    with open(file_path, 'w') as file:
        file.write(gpx.to_xml())

# Fix errors in the GPX data
def fix_gpx_errors(gpx):
    cleaned_gpx = gpxpy.gpx.GPX()

    for track in gpx.tracks:
        cleaned_track = gpxpy.gpx.GPXTrack()
        for segment in track.segments:
            cleaned_segment = gpxpy.gpx.GPXTrackSegment()
            prev_point = None
            prev_valid_point = None

            for i, point in enumerate(segment.points):
                # Skip points with invalid GPS coordinates
                if abs(point.latitude) < 0.0001 and abs(point.longitude) < 0.0001:
                    continue

                # Skip points with large distances from the previous valid point
                if prev_valid_point and calculate_distance(prev_valid_point.latitude, prev_valid_point.longitude, point.latitude, point.longitude) > 1000:
                    continue

                # Skip points with unrealistic time gaps
                if prev_valid_point and point.time and prev_valid_point.time and (point.time - prev_valid_point.time).total_seconds() > 3600:
                    continue

                # Handle uncalibrated timestamps
                if not point.time or point.time.timestamp() == 0:
                    if prev_point and prev_point.time and prev_valid_point and prev_valid_point.time:
                        point.time = interpolate_time(prev_valid_point.time, prev_point.time, prev_valid_point_idx, i, i)
                    elif prev_valid_point and prev_valid_point.time:
                        point.time = prev_valid_point.time + datetime.timedelta(seconds=1)

                cleaned_segment.points.append(point)
                prev_valid_point = point
                prev_valid_point_idx = i
                prev_point = point

            cleaned_track.segments.append(cleaned_segment)
        cleaned_gpx.tracks.append(cleaned_track)

    return cleaned_gpx

# Main function to clean a GPX file
def clean_gpx_file(input_file, output_file):
    gpx = load_gpx(input_file)
    cleaned_gpx = fix_gpx_errors(gpx)
    save_gpx(cleaned_gpx, output_file)
