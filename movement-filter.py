import argparse
import csv

from collections import defaultdict
from scipy.optimize import linear_sum_assignment


def calculate_distance(bb1, bb2):
    center1 = ((int(bb1[1]) + int(bb1[3])) / 2, (int(bb1[2]) + int(bb1[4])) / 2)
    center2 = ((int(bb2[1]) + int(bb2[3])) / 2, (int(bb2[2]) + int(bb2[4])) / 2)
    return ((center1[0] - center2[0]) ** 2 + (center1[1] - center2[1]) ** 2) ** 0.5


def group_tracks(csv, max_distance):
    labels = defaultdict(list)

    with open(csv, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            frame = int(row["frame"])  # Convert to integer for proper sorting
            labels[frame].append(
                [frame, row["xmin"], row["ymin"], row["xmax"], row["ymax"]]
            )

    live_tracks = defaultdict(list)
    done_tracks = defaultdict(list)

    # Initialize tracks with the first frame
    for i, label in enumerate(labels["1"]):
        live_tracks[i] = [label]

    # Iterate through the remaining frames
    for frame in sorted(labels.keys(), key=int)[1:]:
        current_labels = labels[frame]
        distances = []

        # Generate the distance matrix
        for label in current_labels:
            distances.append(
                [calculate_distance(label, track[-1]) for track in live_tracks.values()]
            )

        # Apply the Hungarian algorithm
        label_indices, track_indices = linear_sum_assignment(distances)

        matched_tracks = set()
        for label_idx, track_idx in zip(label_indices, track_indices):
            if distances[label_idx][track_idx] < max_distance:
                track_id = list(live_tracks.keys())[track_idx]
                live_tracks[track_id].append(current_labels[label_idx])
                matched_tracks.add(track_id)

        # Handle unmatched labels and tracks
        unmatched_labels = [
            label for i, label in enumerate(current_labels) if i not in label_indices
        ]
        for label in unmatched_labels:
            live_tracks[max(live_tracks.keys(), default=-1) + 1] = [label]

        # Move unmatched tracks to done_tracks
        for track_id in list(live_tracks):
            if track_id not in matched_tracks:
                done_tracks[track_id] = live_tracks[track_id]
                del live_tracks[track_id]

    # Move all remaining live tracks to done tracks
    for track_id, track in live_tracks.items():
        done_tracks[track_id] = track

    return done_tracks


def filter_tracks(group_tracks, min_distance, min_frames_flip_flop):
    filtered_tracks = defaultdict(list)

    for track_id, track in group_tracks.items():
        segment = []  # Current segment of movement or stillness
        still_counter = 0  # Number of consecutive frames the baboon has been still
        move_counter = 0  # Number of consecutive frames the baboon has been moving
        is_moving = True  # Whether the baboon is currently moving or not

        for i in range(len(track) - 1):
            displacement = calculate_distance(track[i], track[i + 1])

            if displacement >= min_distance:
                move_counter += 1
                still_counter = 0

                # Check if the baboon has resumed moving after being still
                if is_moving or move_counter >= min_frames_flip_flop:
                    segment.append(track[i])
                    is_moving = True  # Affirm movement
            else:
                still_counter += 1
                move_counter = 0

                # Check if the baboon has stopped after moving
                if not is_moving or still_counter >= min_frames_flip_flop:
                    if is_moving and segment:  # Close off the moving segment
                        filtered_tracks[track_id].append(segment)
                        segment = []
                    is_moving = False  # Deny movement

        # Handle the last element of any ongoing segment
        if (
            is_moving and not segment
        ):  # Append the last point if it's moving or if segment is empty
            segment.append(track[-1])
        if segment:
            filtered_tracks[track_id].append(segment)

    return filtered_tracks


def write_tracks_to_csv(filtered_tracks, output_csv):
    with open(output_csv, "w", newline="") as csvfile:
        fieldnames = ["frame", "xmin", "ymin", "xmax", "ymax"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for _, segments in filtered_tracks.items():
            for segment in segments:
                for bbox in segment:
                    writer.writerow(
                        {
                            "frame": bbox[0],  # Frame number
                            "xmin": bbox[1],  # xmin
                            "ymin": bbox[2],  # ymin
                            "xmax": bbox[3],  # xmax
                            "ymax": bbox[4],  # ymax
                        }
                    )


def __main__():
    parser = argparse.ArgumentParser(description="Remove baboons that are not moving.")
    parser.add_argument(
        "csv", type=str, help="CSV file containing bounding box coordinates."
    )
    parser.add_argument(
        "max_distance",
        type=int,
        help="Max distance two labels for the same baboon can be apart (in pixels).",
    )
    parser.add_argument(
        "min_distance",
        type=int,
        help="Min distance a baboon must travel to be considered moving (in pixels).",
    )
    parser.add_argument(
        "min_frames_flip_flop",
        type=int,
        help="Min number of consecutive frames a baboon must be still or moving to change state.",
    )

    args = parser.parse_args()

    input_csv = args.csv
    max_distance = args.max_distance
    min_distance = args.min_distance
    min_frames_flip_flop = args.min_frames_flip_flop

    grouped_tracks = group_tracks(input_csv, max_distance)
    filtered_tracks = filter_tracks(grouped_tracks, min_distance, min_frames_flip_flop)

    write_tracks_to_csv(filtered_tracks)


if __name__ == "__main__":
    __main__()
