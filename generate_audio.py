import logging
import sys
import os
from dotenv import load_dotenv 
import csv
from nanoid import generate
from typing import List, Dict, Any
import polars as pl
import subprocess
import boto3
from botocore.exceptions import TokenRetrievalError
from polly_wrapper import PollyWrapper

def log_audio_map(
        text_audio_map: str,
        file_storage_dir: str, 
        file_log_name: str
    ):
    """
    Log the mappings of text to audio filenames to a CSV file.

    :param text_audio_map: A dictionary mapping audio filenames to text.
    :param file_storage_dir: The directory to store the log file.
    :param file_log_name: The name of the log file.
    """

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

def write_text_to_audio(
        profile_name: str,
        polly_wrapper: PollyWrapper, 
        text: str, 
        output_filename: str, 
        engine: str, 
        voice: str, 
        audio_format: str,
        lang_code: str
    ):
    """
    Synthesizes and writes the given text to audio and saves the output locally.

    :param profile_name: The AWS profile name to use for authentication.
    :param polly_wrapper: An instance of PollyWrapper.
    :param text: The text to synthesize.
    :param output_filename: The filename to save the audio locally.
    :param engine: The engine type.
    :param voice: The voice ID to use for synthesis.
    :param audio_format: The audio format.
    :param lang_code: The language code for the text.

    :return: True if the audio was successfully written to the output file, False otherwise.
    """
    audio_stream = None
    write_success = False
    try:
        # Synthesize given text to audio
        audio_stream, _ = polly_wrapper.synthesize(
            text=text,
            engine=engine,
            voice=voice,
            audio_format=audio_format,
            lang_code=lang_code
        )
    except TokenRetrievalError as e:
        logging.error(f"Failed to retrieve token: {e}")
        logging.info("Attempting to re-authenticate with AWS SSO.")
        authenticate_aws_sso(profile_name)
    except Exception as e:
        logging.error(f"Failed to synthesize audio: {e}")

    # Save the audio stream locally
    if audio_stream:
        try:
            with open(output_filename, "wb") as audio_file:
                audio_file.write(audio_stream.read())
            write_success = True
            logging.info(f"Audio saved to {output_filename}")
        except Exception as e:
            logging.error(f"Failed to save audio to {output_filename}: {e}")
    else:
        logging.error("Audio stream is None. No file was saved.")

    return write_success

def get_request_texts() -> List[Dict[str, Any]]:
    """
    Helper function to retrieve the pieces of text to convert to audio.

    :return: A list of dictionaries containing the request_id, text_speaker, and request_text.
    """
    num_rows = 2
    schema = {
        "request_id": pl.Int64,
        "text_speaker": pl.Utf8,
        "request_text": pl.Utf8
    }
    data = {
        "request_id": range(1, num_rows + 1),
        "text_speaker": ["Joanna" for _ in range(num_rows)],
        "request_text": [
            "The path to discovery is rarely a straight line. Throughout history, explorers have ventured into the unknown, driven by an unyielding curiosity and a desire to uncover the secrets of our world. From the icy tundras of the North to the vast deserts of the Sahara, each journey held the promise of wonder, danger, and knowledge. And while their paths were fraught with challenges, each step brought new insights that reshaped our understanding of the Earth and the cosmos beyond.",
            "The natural world is a delicate web of interconnected life, each species playing a vital role in the ecosystem. From the towering trees of the rainforest to the coral reefs teeming with colorful fish, our planet is a masterpiece of biodiversity. However, human activity has strained this balance, leading to habitat destruction, climate change, and species extinction. Conservation efforts are essential to preserving this fragile balance, ensuring that future generations can experience the awe and beauty of the world as we know it today."
        ]
    }

    req_texts_df = pl.DataFrame(data, schema)

    req_texts_dicts = req_texts_df.to_dicts()

    return req_texts_dicts

def authenticate_aws_sso(
        profile_name: str
    ):
    """
    Authenticate with AWS SSO using the specified profile name.

    :param profile_name: The AWS profile name to use for authentication.
    """
    try:
        subprocess.run(["aws", "sso", "login", "--profile", profile_name])
        logging.info("Successfully authenticated with AWS SSO.")
    except Exception as e:
        logging.error(f"Failed to authenticate with AWS SSO: {e}")

def get_polly_wrapper(
        profile_name: str
    ) -> PollyWrapper:
    """
    Get a PollyWrapper object for interacting with the AWS Polly service.
    
    :param profile_name: The AWS profile name to use for authentication.

    :return: A PollyWrapper object.
    """
    attempts = 0
    max_auth_attempts = 2
    while attempts < max_auth_attempts:
        try:
            # Create a session and clients
            session = boto3.Session(profile_name=profile_name)
            polly_client = session.client("polly")
            s3_resource = session.resource("s3")

            # Initialize and return the PollyWrapper object
            polly = PollyWrapper(polly_client, s3_resource)
            return polly
        except:
            if attempts < max_auth_attempts:
                logging.info(f"SSO session expired. Attempt {attempts + 1} of {max_auth_attempts} to re-authenticate.")
                authenticate_aws_sso(profile_name)
            attempts += 1

    # When max authentication attempts are reached
    logging.error("Max retries reached. Unable to authenticate.")
    logging.error("No PollyWrapper object returned. Exiting.")
    sys.exit(1)

def configure_logging(
        logging_dir: str, 
        logging_file: str
    ):
    """
    Configures the logging settings for the application.

    :param logging_dir: The directory to store the log files.
    :param logging_file: The name of the log file.
    """
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

    :return: A dictionary containing the environment variables.
    """
    load_dotenv()
    return {
        "AWS_PROFILE": os.environ["AWS_PROFILE"]
    }

def main():
    """
    Main function to write pieces of text to audio files.
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

    # Get Polly client for text-to-speech conversion
    profile_name = env_vars["AWS_PROFILE"]
    polly = get_polly_wrapper(profile_name=profile_name)

    # Define pieces of text to convert to audio
    req_texts_dicts = get_request_texts()

    # Process each piece of text and convert to audio
    text_audio_map = {}
    for row in req_texts_dicts:
        # Extract relevant information
        request_id = row["request_id"]
        text_speaker = row["text_speaker"]
        req_text = row["request_text"]

        # Generate a unique ID for the audio file
        unique_id = generate(size=12)
        output_file = os.path.join(file_storage_dir, f"{unique_id}_{text_speaker}.mp3")
        
        # Process the request
        logging.info(f"Processing request ID: {request_id}")
        write_success = write_text_to_audio(
            profile_name=profile_name,
            polly_wrapper=polly,
            text=req_text,
            output_filename=output_file,
            engine="standard",
            voice=text_speaker,
            audio_format="mp3",
            lang_code="en-US"
        )
        if write_success:
            text_audio_map[output_file] = req_text
        else:
            logging.error(f"Failed to process request ID: {request_id}")

    # Log locations of audio and associated text
    log_audio_map(
        text_audio_map, 
        file_storage_dir, 
        file_log_name="audio_to_text_map.csv"
    )

if __name__ == "__main__":
    main()