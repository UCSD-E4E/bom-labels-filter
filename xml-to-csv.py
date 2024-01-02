import xml.etree.ElementTree as ET
import csv
import os
import argparse


def __main__():
    # Set up the argument parser
    parser = argparse.ArgumentParser(description="Convert XML labels to single CSV.")
    parser.add_argument("directory", type=str, help="Directory containing XML files.", default="frames_Annotations")
    args = parser.parse_args()

    # Directory where the XML files are located
    directory = args.directory

    # CSV file to write the data to
    output_csv = "labels.csv"

    # Column names for the CSV file
    columns = ["frame", "xmin", "ymin", "xmax", "ymax"]

    # Open the CSV file once, and write all data
    with open(output_csv, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(columns)

        # Iterate through all XML files in the directory
        for filename in os.listdir(directory):
            if filename.endswith(".xml"):
                # Construct the full file path
                filepath = os.path.join(directory, filename)

                # Parse the XML file
                tree = ET.parse(filepath)
                root = tree.getroot()

                # Get the frame number from the filename element and convert it to an integer
                frame = int(root.find("filename").text)

                # Iterate through each baboon in the XML
                for baboon in root.iter("object"):
                    # Extract and write the bounding box coordinates to the CSV, converting them to integers
                    bndbox = baboon.find("bndbox")
                    x1 = int(float(bndbox.find("xmin").text))
                    y1 = int(float(bndbox.find("ymin").text))
                    x2 = int(float(bndbox.find("xmax").text))
                    y2 = int(float(bndbox.find("ymax").text))

                    # Write the row to the CSV file
                    writer.writerow([frame, x1, y1, x2, y2])

    csvfile.close()


if __name__ == "__main__":
    __main__()
