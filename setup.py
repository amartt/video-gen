import os
import subprocess
import filecmp
from typing import List

def update_file(
        temp_file: str,
        req_filepath: str
    ):
    """
    Updates req_filepath file if there are new changes to temp_filepath
    """
    
    # If req_filepath doesn't exist or differs from temp file, replace it with the temp_file
    # If not, remove temp_file that was generated
    if not os.path.exists(req_filepath) or not filecmp.cmp(temp_file, req_filepath):
        os.replace(temp_file, req_filepath)
    else:
        os.remove(temp_file)

def generate_requirements(
        file: str 
    ):
    """
    Generates a requirements file with sorted dependencies.
    """
    result = subprocess.run(
        ["pip", "freeze"],
        capture_output=True,
        text=True,
        check=True
    )
    with open(file, 'w') as f:
        f.write('\n'.join(sorted(result.stdout.splitlines())))
    return file

def create_env_template(
        env_file: str,
        template_file: str
    ):
    """
    Creates a env template file based on an existing env file
    """
    with open(env_file, 'r') as src:
        lines = []

        for line in src:
            # Ignore empty lines or comments
            if not line.strip() or line.strip().startswith('#'):
                lines.append(line)  # Store without trailing newlines
                continue
            # Split the line at the '=' and keep only the key
            if '=' in line:
                key = line.split('=', 1)[0]
                lines.append(f"{key}=")

    # Write the lines to the template file, joined without a trailing newline
    with open(template_file, 'w') as dest:
        dest.write("\n".join(lines))

    return template_file

def copy_gitignore_to_dockerignore(
        additional_excludes: List,
        git_ignore_path: str,
        docker_ignore_path: str
    ):
    """
    Copies .gitignore content to .dockerignore and adds any additional excludes
    """

    with open(git_ignore_path, 'r') as git_file:
        gitignore_content = git_file.readlines()

    # Add any additional excludes
    additional_excludes_content = [f"{line}\n" for line in additional_excludes]

    # Combine content and write to .dockerignore
    with open(docker_ignore_path, 'w') as docker_ignore_file:
        docker_ignore_file.writelines(additional_excludes_content)
        docker_ignore_file.write('\n')
        docker_ignore_file.writelines(gitignore_content)
    return docker_ignore_path

def main():
    # Reused filenames
    git_ignore_file = ".gitignore"
    docker_ignore_file = ".dockerignore"
    env_template = ".env-template"

    # Additional files to be excluded from the Docker image
    additional_excludes = [
        "# Additional files to be excluded",
        docker_ignore_file,
        "Dockerfile",
        ".git",
        git_ignore_file,
        "setup.py",
        "README.md",
        env_template
    ]
    # Check existing gitignore file and overwrite dockerignore if there are updates
    temp_docker_ignore_file = copy_gitignore_to_dockerignore(
        additional_excludes,
        git_ignore_path=git_ignore_file,
        docker_ignore_path=f"{docker_ignore_file}-temp"
    )
    update_file(
        temp_docker_ignore_file,
        req_filepath=docker_ignore_file
    )

    # Check existing env file and overwrite template if there are updates
    temp_env_template_file = create_env_template(
        env_file=".env", 
        template_file=f"{env_template}-temp"
    )
    update_file(
        temp_env_template_file,
        req_filepath=env_template
    )

    # Check existing packages from the python environment and overwrite requirements if there are updates
    temp_requirements_file = generate_requirements(
        file="temp_requirements.txt"
    )
    update_file(
        temp_requirements_file,
        req_filepath="requirements.txt"
    )

if __name__ == "__main__":
    main()