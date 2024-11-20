"""
Interactive Package Cleanup Tool

This script provides an interactive way to identify and remove all packages
and their dependencies in the current Python environment that are not listed 
in the `requirements.txt` file. 

Requirements:
- `requirements.txt` file must be present in the same directory as the script.
- The `pipdeptree` package must be installed to analyze package dependencies.
"""

import subprocess
import re
from typing import Optional, Set

def style_text(
        text: str,
        color: Optional[str] = None,
        bold: bool = False,
        underline: bool = False,
        background: Optional[str] = None
    ):
    """
    Apply ANSI styles to text for printed output.

    :param text: The text to style.

    :param color: The text color. Options: 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'.

    :param bold: Apply bold styling if True.
    
    :param underline: Apply underline styling if True.
    
    :param background: The background color. Same options as `color`.
    """
    ansi_codes = []
    
    # Define color codes
    colors = {
        "black": 30, "red": 31, "green": 32, "yellow": 33,
        "blue": 34, "magenta": 35, "cyan": 36, "white": 37
    }
    backgrounds = {color: code + 10 for color, code in colors.items()}

    # Append specified codes
    if color and color in colors:
        ansi_codes.append(str(colors[color]))
    if background and background in backgrounds:
        ansi_codes.append(str(backgrounds[background]))
    if bold:
        ansi_codes.append("1")
    if underline:
        ansi_codes.append("4")

    # Combine all codes and wrap the text
    ansi_start = f"\033[{';'.join(ansi_codes)}m" if ansi_codes else ""
    ansi_end = "\033[0m"

    print(f"{ansi_start}{text}{ansi_end}")

def is_valid_package_name(
        line: str
    ) -> bool:
    """
    Checks if a given line of text begins with a valid package name.

    Begins with a letter, digit, underscore, or hyphen.
    """
    pattern = r'^[a-zA-Z0-9_-]'
    return re.match(pattern, line) is not None

def parse_requirements_file(
        filepath: str
    ) -> Set[str]:
    """
    Parse requirements file to extract package names.
    """
    packages = set()
    with open(filepath, "r") as file:
        for line in file:
            package_name = line.split("==")[0]
            packages.add(package_name)
    return packages

def get_installed_packages() -> Set[str]:
    """
    Get all installed packages in the environment.
    """
    packages = set()
    package_output = subprocess.run(
        ["pip", "freeze"],
        capture_output=True,
        text=True,
        check=True
    )

    package_output_lines = package_output.stdout.splitlines()
    for line in package_output_lines:
        package_name = line.split("==")[0]
        packages.add(package_name)
    
    return packages

def get_independent_packages() -> Set[str]:
    """
    Get independent packages from the dependency tree of installed packages.
    """
    # Run subprocess to get dependency tree of installed packages
    dep_tree_output = subprocess.run(
        ["pipdeptree"],
        capture_output=True,
        text=True,
        check=True
    )
    dep_tree_output_lines = dep_tree_output.stdout.splitlines()

    # Identify all installed packages without any dependencies in the tree
    independent_packages = set()
    for line in dep_tree_output_lines:
        if is_valid_package_name(line):
            package_name = line.split("==")[0]
            independent_packages.add(package_name)

    return independent_packages

def get_new_independent_packages(
        requirements_filepath: str
    ) -> Set[str]:
    """
    Based on known package requirements in the requirements file and all installed packages in the environment, return all newly installed packages which do not have have any dependencies.
    """
    # Get all packages from the requirements file
    current_packages = parse_requirements_file(requirements_filepath)

    # Get all installed packages in the environment
    installed_packages = get_installed_packages()

    # Find all installed packages which are not included in the requirements file
    new_packages = installed_packages - current_packages

    # Identify all installed packages without any dependencies
    dependency_free_packages = get_independent_packages()

    # Return all newly installed packages which have no dependencies
    return new_packages & dependency_free_packages

def main():
    req_filepath = "requirements.txt"

    # Identify all newly installed packages which do not have any dependencies
    style_text(
        text="Identifying independent packages...",
        color="cyan",
        bold=True
    )
    packages_of_interest = get_new_independent_packages(
        requirements_filepath=req_filepath
    )
    print(f"Independent packages: {packages_of_interest}")

    # Get user input to keep any amount of the new packages
    packages_to_keep = set()
    while True:
        user_input = input("Enter a package to keep (type 'n' when finished): ").strip()
        if user_input == 'n':
            break
        if user_input:
            packages_to_keep.add(user_input)

    # Iteratively remove new packages that do not want to be kept and all unneeded dependencies
    while True:
        # Re-identify all new packages which do not have any dependencies
        style_text(
            text="\nRe-identifying independent packages...",
            color="yellow",
            bold=True
        )
        packages_of_interest = get_new_independent_packages(
            requirements_filepath=req_filepath
        )

        # Uninstall each package without a confirmation
        packages_to_uninstall = packages_of_interest - packages_to_keep
        if packages_to_uninstall:
            print(f"Packages to uninstall: {packages_to_uninstall}")
            for package in packages_to_uninstall:
                style_text(
                    text=f"\nUninstalling {package}...",
                    color="red",
                    bold=True
                )
                subprocess.run(["pip", "uninstall", "-y", package])
        else:
            style_text(
                text="\nNo more packages to uninstall.",
                color="green",
                bold=True
            )
            break

if __name__ == "__main__":
    main()