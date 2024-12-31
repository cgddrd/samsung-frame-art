import sys
import logging
import os
import random
import json
import argparse
import wakeonlan
import time
import requests
import random
import shutil
import io
from PIL import Image, ImageStat

sys.path.append("../")
from samsungtvws import SamsungTVWS

def is_image_dark(image_path):
    """
    Check whether an image is mainly dark or light.
    Returns True if the image is mainly dark, otherwise False.
    """
    image = Image.open(image_path).convert("L")  # Convert to grayscale
    stat = ImageStat.Stat(image)
    average_brightness = stat.mean[0]  # Get the average brightness (0-255)
    return average_brightness < 85  # Threshold for darkness (127 is midway in 0-255)

def set_image_on_tv(tv, remote_filename):
    show_image = is_artwork_display_possible(tv)
    tv.art().select_image(remote_filename, show=show_image)


def is_artmode_active(tv):
    return tv.art().get_artmode() == "on"


def is_artwork_display_possible(tv):
    return tv.on() and is_artmode_active(tv)


def download_random_landscape_images(dir, image_size):
    # Delete the directory if it exists
    if os.path.exists(dir):
        shutil.rmtree(dir)
    
    # Recreate the directory
    os.makedirs(dir)

    # https://unsplash.com/@susan_wilkinson
    collections = ["8262542", "879220", "1976117", "2027881", "4494328", "1887125", "32519533"]

    url = "https://api.unsplash.com/photos/random"
    headers = {
        "Authorization": f"Client-ID {UNSPLASH_API_KEY}"
    }
    
    params = {
        "count": 1,
        "orientation": "landscape",
        "collections": random.choice(collections)
    }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    
    if response.status_code != 200 or not isinstance(data, list):
        print(f"Error fetching data from Unsplash API {response}")
        return

    # Create the directory if it doesn't exist
    os.makedirs(dir, exist_ok=True)
    
    for i, photo in enumerate(data):
        
        # Select the URL for the specified image size
        image_url = photo['urls'][image_size]
        
        # Download the image
        image_data = requests.get(image_url).content
        timestamp = int(time.time())
        file_name = f"{dir}/iotd{timestamp}.jpg"

        # Open the image with PIL
        image = Image.open(io.BytesIO(image_data))
        
        ## Target dimensions
        target_width = 3840
        target_height = 2160

        # Calculate scale factor to cover the target size
        scale_width = target_width / image.width
        scale_height = target_height / image.height
        scale = max(scale_width, scale_height)  # Use max to ensure the image covers the target size
        
        # Resize the image while preserving aspect ratio
        new_width = int(image.width * scale)
        new_height = int(image.height * scale)
        image = image.resize((new_width, new_height), Image.LANCZOS)
        
        # Crop the center of the image to the target dimensions
        left = (image.width - target_width) // 2
        top = (image.height - target_height) // 2
        right = left + target_width
        bottom = top + target_height
        image = image.crop((left, top, right, bottom))

        # Save the processed image
        image.save(file_name, format='JPEG')
        print(f"Downloaded and processed: {file_name}")

SELECTED_MATTE = "none"
MATTE_TYPE="modernthin"
LIGHT_MODE_MATTE = f"{MATTE_TYPE}_warm"
DARK_MODE_MATTE = "none"

# Add command line argument parsing
parser = argparse.ArgumentParser(description="Upload images to Samsung TV.")
parser.add_argument(
    "--debug", action="store_true", help="Enable debug mode to check if TV is reachable"
)
parser.add_argument(
    "--unsplash-api-key", type=str, required=True, help="Unsplash API key for downloading images"
)
parser.add_argument(
    "--ip", type=str, required=True, help="IP address of the Samsung TV"
)
parser.add_argument(
    "--mac", type=str, required=True, help="MAC address of the Samsung TV"
)
args = parser.parse_args()

# Use the provided Unsplash API key and TV IP
UNSPLASH_API_KEY = args.unsplash_api_key
TV_IP = args.ip
TV_MAC = args.mac

rand_no = random.random() 
if rand_no < 0.5:
    folder_path = './downloaded'
    download_random_landscape_images(folder_path, image_size='full')
else:
    # Set the path to the folder containing the images
    folder_path = "./frameart"

# Set the path to the file that will store the list of uploaded filenames
upload_list_path = "./uploaded_files.json"

# Load the list of uploaded filenames from the file
if os.path.isfile(upload_list_path):
    with open(upload_list_path, "r") as f:
        uploaded_files = json.load(f)
else:
    uploaded_files = []


print("Waking up TV.")
wakeonlan.send_magic_packet(TV_MAC)

print("Waiting 10 secs...")
time.sleep(10)

# Set your TV's local IP address. Highly recommend using a static IP address for your TV.
tv = SamsungTVWS(TV_IP)

print(tv.rest_device_info())

print(tv.art().get_matte_list())

print(tv.art().get_photo_filter_list())

# Check if TV is reachable in debug mode
if args.debug:
    try:
        print("Checking if the TV can be reached.")
        info = tv.rest_device_info()
        print("If you do not see an error, your TV could be reached.")
        sys.exit()
    except Exception as e:
        logging.error("Could not reach the TV: " + str(e))
        sys.exit()

# Check if the TV supports art mode
art_mode = tv.art().supported()

if art_mode:
    # Retrieve information about the currently selected art
    current_art = tv.art().get_current()

    # Get a list of JPG/PNG files in the folder (including subdirectories if applicable)
    files = [
        os.path.join(root, f)
        for root, _, filenames in os.walk(folder_path)
        for f in filenames
        if f.endswith((".jpg", ".jpeg", ".png"))
    ]

    print("Choosing random image.")
    files_to_upload = [random.choice(files)]

    for file in files_to_upload:

        # Determine if the image is dark or light
        is_dark = is_image_dark(file)
        SELECTED_MATTE = DARK_MODE_MATTE if is_dark else LIGHT_MODE_MATTE
        print(f"Image {file} is {'dark' if is_dark else 'light'}. Setting SELECTED_MATTE to {SELECTED_MATTE}.")

        # Read the file contents
        with open(file, "rb") as f:
            data = f.read()

        # Check if the file is already uploaded
        remote_filename = None
        for uploaded_file in uploaded_files:
            if uploaded_file["file"] == file:
                remote_filename = uploaded_file["remote_filename"]
                print("Image already uploaded.")
                break
        
        print(remote_filename)
        if remote_filename is None:
            print("Uploading new image: " + str(file))
            try:
                if file.endswith((".jpg", ".jpeg")):
                    remote_filename = tv.art().upload(
                        data, file_type="JPEG", matte=SELECTED_MATTE
                    )
                elif file.endswith(".png"):
                    remote_filename = tv.art().upload(
                        data, file_type="PNG", matte=SELECTED_MATTE
                    )
            except Exception as e:
                logging.error("There was an error: " + str(e))
                sys.exit()

            # Add the file to the uploaded list
            uploaded_files.append({"file": file, "remote_filename": remote_filename})

            # Select the uploaded image
            set_image_on_tv(tv, remote_filename)
        else:
            # Select the existing image
            print("Setting existing image, skipping upload")
            set_image_on_tv(tv, remote_filename)

        # Save the uploaded files list
        with open(upload_list_path, "w") as f:
            json.dump(uploaded_files, f)
else:
    logging.warning("Your TV does not support art mode.")
