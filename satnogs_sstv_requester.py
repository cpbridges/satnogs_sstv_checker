import requests
import os
import cv2  # OpenCV for image processing
import numpy as np
from datetime import datetime

API_URL = "https://network.satnogs.org/api/observations/" # Base URL for the SATNOGS API

# ANSI escape codes for colored output
GREEN = "\033[92m"  # Green text
RED = "\033[91m"    # Red text
RESET = "\033[0m"   # Reset text color to default

def download_image(image_url, save_dir="satnogs_images"): # Function to download a file from a URL
    
    os.makedirs(save_dir, exist_ok=True) # Make sure the directory exists

    image_name = image_url.split("/")[-1] # Extract the image file name from the URL
    save_path = os.path.join(save_dir, image_name)

    response = requests.get(image_url) # Download the image
    if response.status_code == 200:
        with open(save_path, "wb") as f:
            f.write(response.content)
        print(f"Downloaded image: {save_path}")
        return save_path  # Return the saved image path for further analysis
    else:
        print(f"Failed to download {image_url}. Status code: {response.status_code}")
        return None

# Function to analyze an image to determine if it's static or has content
def is_static_image(image_path, threshold=20000):
    
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE) # Load the image in grayscale mode

    if img is None:
        print(f"Error loading image {image_path}")
        return True  # If the image can't be loaded, assume it's static

    laplacian_var = cv2.Laplacian(img, cv2.CV_64F).var() # Apply the Laplacian operator to detect edges and calculate variance

    print(f"Variance of Laplacian for {image_path}: {laplacian_var}")

    return laplacian_var > threshold # If the variance is below the threshold, we consider the image static

# Function to retrieve and download SSTV images from a given observation within a date range
def get_sstv_images(station_id, satellite_id=25544, start_date=None, end_date=None, limit=10):
    # Build the API query URL
    params = {
        "norad_cat_id": satellite_id,  # ISS (Sat ID 25544)
        "ground_station": station_id,
        "status": "good",  # We want only "good" observations
        "limit": limit,
        "transmitter_mode": "SSTV",
    }

    # If using date range, add to the query
    if start_date:
        params["start"] = start_date.isoformat()  # Format date in ISO 8601
    if end_date:
        params["end"] = end_date.isoformat()

    # Send the request to the SATNOGS API
    response = requests.get(API_URL, params=params)
    if response.status_code != 200:
        print(f"Failed to retrieve observations. Status code: {response.status_code}")
        return
    
    observations = response.json() # Parse the response JSON

    for obs in observations: # Loop through observations and download images
        observation_id = obs["id"]
        print(f"Processing observation {observation_id}...")

        decoded_data = obs.get("demoddata", []) # Check if there are any decoded images
        for data in decoded_data:

            image_url = data["payload_demod"]
            image_path = download_image(image_url)

            if image_path: # If the image was downloaded successfully, analyze it
                if is_static_image(image_path):
                    print(f"{RED}Image {image_path} appears to be static (noise).{RESET}")
                    os.remove(image_path)
                else:
                    print(f"{GREEN}Image {image_path} contains content (image).{RESET}")

# Main function to run the script
if __name__ == "__main__":
    
    station_id = 2433  # SSC Groundstation

    # start_date_str = input("Enter start date (YYYY-MM-DD): ") # Input the date range
    # end_date_str = input("Enter end date (YYYY-MM-DD): ")
    
    start_date_str = ('2024-10-01')
    end_date_str = ('2024-10-17')

    try: # Convert the date strings to datetime objects
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")
        exit(1)

    # Retrieve and download SSTV images between the given dates
    get_sstv_images(station_id, start_date=start_date, end_date=end_date)