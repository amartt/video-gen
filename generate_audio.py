import requests 
import base64 
import logging
import sys
import os
from dotenv import load_dotenv 
import re 
import textwrap
import tempfile
import csv

load_dotenv()

# Credit to oscie57 for the sourced environment variables and values. See README for more details.
API_BASE_URL = os.environ["API_BASE_URL"]
USER_AGENT = os.environ["USER_AGENT"]
CHARACTER_LIMIT = int(os.environ["CHARACTER_LIMIT"])
SPEAKER_MAP_TYPE = int(os.environ["SPEAKER_MAP_TYPE"])
AID = int(os.environ["AID"])

def text_to_speech(
        session_id: str, 
        text_speaker: str, 
        req_text: str,
        filename: str
    ):

    # Define request parameters
    params = {
        'text_speaker': text_speaker,
        'req_text': req_text,
        'speaker_map_type': SPEAKER_MAP_TYPE,
        'aid': AID
    }

    # Define request headers
    headers = {
        'User-Agent': USER_AGENT,
        'Cookie': f'sessionid={session_id}'
    }

    try:
        # Make the request
        response = requests.post(
            url=API_BASE_URL,
            headers=headers,
            params=params
        )

        # Process the response
        if response.status_code == 200:
            try:
                response_json = response.json()
            except ValueError:
                logging.error("Failed to decode JSON from response.")
                sys.exit(1)
        else:
            logging.error(f"Request failed with status code: {response.status_code}.\nResponse content: {response.text}")
            sys.exit(1)
            
    except Exception as e:
        logging.error(f"Request failed due to an exception: {e}")
        sys.exit(1)
    
    status_code_lookup = {
        None: "No status code recieved",
        0: "Response is valid and processed successfully",
        1: "Invalid 'aid' value or missing 'text_speaker' or 'req_text' parameters",
        2: "'req_text' exceeds the character limit",
        3: "Unknown issue encountered",
        4: "Invalid 'text_speaker' parameter value"
    }
    status_code = response_json.get("status_code", None)
    status_code_message = status_code_lookup.get(status_code, f"Unknown status code: {status_code}")
    if status_code != 0:
        logging.error(f"{status_code_message}\nFull response: {response_json}")
        sys.exit(1)
    else:
        logging.info(status_code_message)

        voice_str = response_json.get("data", {}).get("v_str", None)
        if voice_str is None:
            logging.error(f"'v_str' is missing from the response, needed to generate audio.\nFull response: {response_json}")
            sys.exit(1)
        else:
            # Write audio contents to file
            decoded_audio_data = base64.b64decode(voice_str)
            try:
                with open(filename, "wb") as out:
                    out.write(decoded_audio_data)
                logging.info(f"Audio successfully written to {filename}")
            except (IOError, OSError) as e:
                logging.error(f"Failed to write audio to {filename}. Error: {e}")
                sys.exit(1)

# def batch_create(batch_storage_path: str, filename: str):
#     out = open(filename, 'wb')

#     def sorted_alphanumeric(data):
#         convert = lambda text: int(text) if text.isdigit() else text.lower()
#         alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
#         return sorted(data, key=alphanum_key)

#     for item in sorted_alphanumeric(os.listdir(batch_storage_path)):
#         filestuff = open(batch_storage_path + item, 'rb').read()
#         out.write(filestuff)

#     out.close()

# def sorted_alphanumeric(data):
#     """
#     Sorts a list in alphanumeric order.
#     """
#     convert = lambda text: int(text) if text.isdigit() else text.lower()
#     alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
#     return sorted(data, key=alphanum_key)

def sorted_alphanumeric(data):
    """
    Sorts a list in alphanumeric order, handling both numeric and alphabetic parts.
    """
    def alphanum_key(key):
        # Split the string into numeric and non-numeric parts
        parts = re.split('([0-9]+)', key)
        # Convert numeric parts to integers and lowercase non-numeric parts
        return [int(part) if part.isdigit() else part.lower() for part in parts]
    
    return sorted(data, key=alphanum_key)

def batch_create(batch_storage_path: str, filename: str):
    """
    Combines all files in the specified directory into a single file.

    Parameters:
    - batch_storage_path: Directory containing the batch files.
    - filename: Output file name.
    """
    with open(filename, 'wb') as out_file:
        for item in sorted_alphanumeric(os.listdir(batch_storage_path)):
            file_path = os.path.join(batch_storage_path, item)
            with open(file_path, 'rb') as f:
                out_file.write(f.read())

def log_created_audio(file_storage_dir, file_log_name):

    filepath = os.path.join(file_storage_dir, file_log_name)
    file_exists = os.path.isfile(filepath)

    # Open the CSV file in append mode
    with open(filepath, 'a', newline='') as f:
        writer = csv.writer(f)

        # If the file doesn't exist, write the header first
        if not file_exists:
            writer.writerow(['Filename', 'Text'])

        # Write each item in the dictionary to the CSV
        for filename, text in audio_mapping.items():
            writer.writerow([filename, text])

def main(file_storage_dir, req_text, filename):

    text_speaker = "en_us_002"
    session_id = "8c00f6a55de19e5393c875c8158914c7"

    chunk_size = CHARACTER_LIMIT
    textlist = textwrap.wrap(req_text, width=chunk_size, break_long_words=True, break_on_hyphens=False)

    # Create a temporary directory
    temp_dir = os.path.join(file_storage_dir, "tmp")
    with tempfile.TemporaryDirectory() as temp_dir:
        # Logic to create temporary audio files in temp_dir
        for index, item in enumerate(textlist):
            text_to_speech(
                session_id, 
                text_speaker, 
                item, 
                os.path.join(temp_dir, f"audio_{index}.mp3")
            )

        # Logic to combine the audio files in temp_dir
        batch_create(temp_dir, filename)

    # temp_dir = os.path.join(file_storage_dir, "tmp")
    # if not os.path.exists(temp_dir):
    #     os.makedirs(temp_dir)

    # for index, item in enumerate(textlist):
    #     text_to_speech(session_id, text_speaker, item, f"{temp_dir}_{index}.mp3")

    # batch_create(temp_dir, filename)

    # # Remove temporary files
    # for item in os.listdir(temp_dir):
    #     os.remove(temp_dir + item)
    # if os.path.exists(temp_dir):
    #     os.removedirs(temp_dir)

if __name__ == "__main__":
    # Configure logging
    logging_dir = "./logs"
    if not os.path.exists(logging_dir):
        os.makedirs(logging_dir)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(logging_dir, "audio_generation.log")),
            logging.StreamHandler()
        ]
    )

    # Handle storage to dump files into
    file_storage_dir = './generated_files'
    if not os.path.exists(file_storage_dir):
        os.makedirs(file_storage_dir)

    # Define pieces of text to convert to audio
    req_texts = [
        "In a quiet corner of the city, there’s a small café where time seems to slow down. The charm is in the details—soft light, mellow music, and the murmur of conversations. It feels like home to everyone."
    ]

    # Process each piece of text and convert to audio
    audio_mapping = {}
    for index, req_text in enumerate(req_texts):
        filename = os.path.join(file_storage_dir, f"audio_{index}.mp3")
        try:
            main(file_storage_dir, req_text, filename)
            audio_mapping[filename] = req_text
        except Exception as e:
            logging.error(f"Failed to convert text to audio {e}: {req_text}")

    log_created_audio(file_storage_dir, "audio_to_text_map.csv")    