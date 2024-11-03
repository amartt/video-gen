import requests 
import base64 
import logging
import sys
import os
from dotenv import load_dotenv 
import textwrap
import tempfile
import csv
from nanoid import generate
from typing import List, Dict, Any
import polars as pl

def log_audio_map(
        text_audio_map: str,
        file_storage_dir: str, 
        file_log_name: str
    ):

    # Check for existence of file
    filepath = os.path.join(file_storage_dir, file_log_name)
    file_exists = os.path.isfile(filepath)

    # Record mappings of text and filenames for the audio
    with open(filepath, 'a', newline='') as f:
        writer = csv.writer(f)

        # If the file doesn't exist, write the header first
        if not file_exists:
            writer.writerow(['Filename', 'Text'])

        # Write each item in the dictionary to the CSV
        for filename, text in text_audio_map.items():
            writer.writerow([filename, text])

def sort_files(file_list: List[str]) -> List[str]:
    # Given that the filenames in file_list are integers, sort them in increasing order
    return sorted(file_list, key=lambda x: int(x.split('.')[0]))

def combine_files(
        storage_path: str, 
        filename: str
    ):
    """
    Combines all files in the specified directory into a single file.

    Parameters:
    - storage_path: Directory containing the files to be combined.
    - filename: Output file name.
    """
    with open(filename, 'wb') as out_file:
        for temp_file in sort_files(os.listdir(storage_path)):
            file_path = os.path.join(storage_path, temp_file)
            with open(file_path, 'rb') as f:
                out_file.write(f.read())

def extract_write_audio_data(
        filename: str,
        response_json: Dict[str, Any]
    ):
    """
    Extracts the audio data from the response and writes it to the inputted filename
    """
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
            logging.error(f"Failed to write audio to {filename}.\nError: {e}")
            sys.exit(1)

def check_tts_status_code(
        response_json: Dict[str, Any]
    ):
    """
    Checks the status code for the audio response
    """
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

def make_post_request(
        session: requests.Session,
        url: str,
        params: Dict[str, str], 
    ) -> Dict[str, Any]:
    """
    Helper function to make a post request and return a response.
    """
    # Make the request
    try:
        response = session.post(
            url=url,
            params=params
        )

        # Process the response
        if response.status_code == 200:
            try:
                return response.json()
            except ValueError:
                logging.error("Failed to decode JSON from response.")
                sys.exit(1)
        else:
            logging.error(f"Request failed with status code: {response.status_code}.\nResponse content: {response.text}")
            sys.exit(1)
            
    except Exception as e:
        logging.error(f"Request failed due to an exception: {e}")
        sys.exit(1)

def get_audio_from_text(
        session: requests.Session,
        env_vars: Dict[str, str],
        text_speaker: str, 
        req_text: str,
        filename: str
    ):
    """
    Function to take text as input and output audio to filename with a text_speaker voice
    """

    # Define request parameters
    params = {
        'text_speaker': text_speaker,
        'req_text': req_text,
        'speaker_map_type': env_vars["SPEAKER_MAP_TYPE"],
        'aid': env_vars["AID"]
    }

    # Make the request and get the response
    response_json = make_post_request(
        session,
        env_vars["API_BASE_URL"],
        params
    )

    # Check the status code
    check_tts_status_code(response_json)

    # Extract and write audio data
    extract_write_audio_data(filename, response_json)

def write_text_to_audio(
        session: requests.Session,
        output_file: str,
        req_text: str, 
        text_speaker: str,
        env_vars: Dict[str, str]
    ):

    # Break apart text based on the character limit for each request
    texts_list = textwrap.wrap(req_text, width=env_vars["CHARACTER_LIMIT"], break_long_words=True, break_on_hyphens=False)

    # Create temporary audio files in temp_dir and combine them into the output_file
    with tempfile.TemporaryDirectory() as temp_dir:
        for index, text in enumerate(texts_list):
            get_audio_from_text(
                session,
                env_vars,
                text_speaker, 
                text, 
                filename=os.path.join(temp_dir, f"{index}.mp3")
            )

        # Combine the temp audio files in temp_dir into the final output_file
        combine_files(temp_dir, output_file)

def get_session_id() -> str:
    """
    Helper function to retrieve the session id, placeholder for now
    """
    return "8c00f6a55de19e5393c875c8158914c7"

def get_request_texts() -> List[Dict[str, Any]]:
    """
    Helper function to retrieve the pieces of text to convert to audio
    """
    num_rows = 3
    schema = {
        "request_id": pl.Int64,
        "text_speaker": pl.Utf8,
        "request_text": pl.Utf8
    }
    data = {
        "request_id": range(1, num_rows + 1),
        "text_speaker": ["en_us_002" for _ in range(num_rows)],
        "request_text": [
            "The path to discovery is rarely a straight line. Throughout history, explorers have ventured into the unknown, driven by an unyielding curiosity and a desire to uncover the secrets of our world. From the icy tundras of the North to the vast deserts of the Sahara, each journey held the promise of wonder, danger, and knowledge. And while their paths were fraught with challenges, each step brought new insights that reshaped our understanding of the Earth and the cosmos beyond.",
            "In the realm of technology, change is the only constant. Innovation has transformed how we communicate, learn, and interact, shrinking the world into a global village. The rise of artificial intelligence, machine learning, and blockchain has sparked a new era, redefining industries and reshaping our everyday lives. As we push forward, we must consider not just what is possible, but also the ethical implications of our advancements, ensuring that technology serves humanity as a force for good.",
            "The natural world is a delicate web of interconnected life, each species playing a vital role in the ecosystem. From the towering trees of the rainforest to the coral reefs teeming with colorful fish, our planet is a masterpiece of biodiversity. However, human activity has strained this balance, leading to habitat destruction, climate change, and species extinction. Conservation efforts are essential to preserving this fragile balance, ensuring that future generations can experience the awe and beauty of the world as we know it today."
        ]
    }

    req_texts_df = pl.DataFrame(data, schema)

    req_texts_dicts = req_texts_df.to_dicts()

    return req_texts_dicts

def configure_logging(
        logging_dir: str, 
        logging_file: str
    ):
    if not os.path.exists(logging_dir):
        os.makedirs(logging_dir)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(logging_dir, logging_file)),
            logging.StreamHandler()
        ]
    )

def load_env_variables() -> Dict[str, str]:
    """
    Loads environment variables and returns them as a dictionary.
    """
    load_dotenv()
    # Credit to oscie57 for the sourced environment variables and values. See README for more details.
    return {
        "API_BASE_URL": os.environ["API_BASE_URL"],
        "USER_AGENT": os.environ["USER_AGENT"],
        "CHARACTER_LIMIT": int(os.environ["CHARACTER_LIMIT"]),
        "SPEAKER_MAP_TYPE": int(os.environ["SPEAKER_MAP_TYPE"]),
        "AID": int(os.environ["AID"])
    }

def main():
    """
    Main function to write pieces of text to audio files
    """
    # Retrieve environment variables
    env_vars = load_env_variables()

    # Configure logging
    configure_logging(
        logging_dir="./logs",
        logging_file="audio_generation.log"
    )

    # Handle storage to dump files into
    file_storage_dir = './generated_files'
    if not os.path.exists(file_storage_dir):
        os.makedirs(file_storage_dir)

    # Define pieces of text to convert to audio
    req_texts_dicts = get_request_texts()

    # Process each piece of text and convert to audio
    text_audio_map = {}
    with requests.Session() as session:
        # Define session headers (constant for all requests)
        session_id = get_session_id()
        session.headers.update(
            {
                'User-Agent': env_vars["USER_AGENT"],
                'Cookie': f'sessionid={session_id}'
            }
        )
        for row in req_texts_dicts:
            req_text = row["request_text"]
            text_speaker = row["text_speaker"]
            unique_id = generate(size=12)
            output_file = os.path.join(file_storage_dir, f"{unique_id}_{text_speaker}.mp3")
            try:
                write_text_to_audio( 
                    session,
                    output_file,
                    req_text, 
                    text_speaker,
                    env_vars
                )
                text_audio_map[output_file] = req_text
            except Exception as e:
                logging.error(f"{e}: Failed to convert given text to audio: {req_text}")
    
    # Log locations of audio and associated text
    log_audio_map(
        text_audio_map, 
        file_storage_dir, 
        file_log_name="audio_to_text_map.csv"
    )

if __name__ == "__main__":
    main()