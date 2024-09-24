import os
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional
from zipfile import ZipFile

import requests


def get_edge_version() -> Optional[str]:
    result = os.popen("microsoft-edge --version").read().strip()
    match = re.search(r"(\d+\.\d+\.\d+\.\d+)", result)
    if match:
        version = match.group(1)
        return version
    return None


def download_webdriver(version: str) -> bool:
    webdriver_url = (
        f"https://msedgedriver.azureedge.net/{version}/edgedriver_linux64.zip"
    )
    response = requests.get(webdriver_url)
    if response.status_code == 200:
        with open("edgedriver_linux64.zip", "wb") as file:
            file.write(response.content)
        return True
    return False


def install_webdriver(install_dir: Path, version: str) -> None:
    with ZipFile("edgedriver_linux64.zip", "r") as zip_ref:
        zip_ref.extractall("/tmp/")
    os.chmod("/tmp/msedgedriver", 0o755)

    # Create the install directory if it does not exist
    install_dir.mkdir(parents=True, exist_ok=True)

    # Move the WebDriver to the install directory with version in the name
    target_path = install_dir / f"msedgedriver_{version}"
    shutil.move("/tmp/msedgedriver", target_path)

    # Create a symlink named "msedgedriver" pointing to the versioned WebDriver
    symlink_path = install_dir / "msedgedriver"
    if symlink_path.exists():
        symlink_path.unlink()
    symlink_path.symlink_to(target_path)

    os.remove("edgedriver_linux64.zip")

    print(f"Symlink created at: {symlink_path}")


def get_available_versions() -> List[str]:
    url = "https://msedgewebdriverstorage.blob.core.windows.net/edgewebdriver?delimiter=%2F&maxresults=100000&restype=container&comp=list&_=1727162272993&timeout=60000"
    response = requests.get(url)
    content = response.content.decode("utf-8-sig")  # Decode with BOM handling
    root = ET.fromstring(content)
    versions = [
        prefix.find("Name").text.strip("/")
        for prefix in root.findall(".//BlobPrefix")
        if prefix.find("Name") is not None
    ]
    return versions


def install_edge_webdriver(install_dir: Path = Path.home() / "bin") -> None:
    # Add the install directory to the PATH if it is not already
    if str(install_dir) not in os.environ["PATH"]:
        os.environ["PATH"] += f":{install_dir}"

    edge_version = get_edge_version()
    if not edge_version:
        print("Microsoft Edge is not installed or the version could not be determined.")
        exit(1)

    print(f"Detected Microsoft Edge version: {edge_version}")
    print("Downloading matching Edge WebDriver...")

    available_versions = get_available_versions()
    if edge_version in available_versions:
        start_index = available_versions.index(edge_version)
    else:
        start_index = 0

    for version in available_versions[start_index:]:
        if download_webdriver(version):
            print(f"Downloaded Edge WebDriver version: {version}")
            print("Installing Edge WebDriver...")
            install_webdriver(install_dir, version)
            print("Edge WebDriver installed successfully!")
            break
    else:
        print(
            "Failed to download and install Edge WebDriver. Please check the available versions and try again."
        )


if __name__ == "__main__":
    install_edge_webdriver()
