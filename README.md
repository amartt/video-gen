# Video Generator
A tool to automate the creation of short and long-form videos with captioning, text-to-speech, and metadata management, enabling highlight generation based on audio and visual cues.

## Installation

### Prerequisites
- [Docker](https://www.docker.com/get-started) installed on your machine
- AWS Profile with Permissions: Ensure you have an AWS CLI profile configured. This profile must use a role or user with the following managed policies:
  - `AmazonPollyFullAccess`
  - `AmazonS3FullAccess`

### Setup Instructions

1. **Configure Environment Variables**: 
   - Copy the `.env-template` file to a `.env` file: 

     ```bash
     cp .env-template .env
     ```
   - Fill out the `.env` file

2. **Build the Docker Image**: 

   ```bash
   docker build -t video-gen-image .
   ```

3. **Run the Docker Container**: 

    ```bash
    docker run -d --name video-gen-container --env-file .env video-gen-image tail -f /dev/null
    ```

## Usage

When the container is running, use the following commands to interact with it

### Run the Project

```bash
docker exec video-gen-container make run
```

### Manage Generated Files

- Logs are stored in the /logs subdirectory
- Generated files are in the /generated_files subdirectory
```bash
docker exec -it video-gen-container /bin/bash
```

### Clean Up

- Clear generated files and logs
```bash
docker exec video-gen-container make clean
```

### Stopping and Restarting

- Stop the container:
    ```bash
    docker stop video-gen-container
    ```

- Restart the container:
    ```bash
    docker start video-gen-container
    ```

<!-- ## Configuration -->

<!-- ## Features -->

<!-- ## License -->

<!-- ## Contributions -->

<!-- ## Testing -->

## Credits
- [Amazon Polly](https://aws.amazon.com/polly/): Used for text-to-speech synthesis in this tool.