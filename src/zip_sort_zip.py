import argparse
import glob
import logging
import os
import shutil
import sys
import tempfile
import time
import zipfile
from datetime import datetime
from typing import (
    List,
    Optional
)

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(level=logging.DEBUG)


def make_folder(folder_path: str) -> None:
    """ Make a folder if it doesn't exist
    :param folder_path: The path to the folder to make
    :return: None
    """
    if not os.path.exists(folder_path):
        logger.info(f"Creating folder: {folder_path}")
        os.makedirs(folder_path)


def get_temp_folder(folder_path: Optional[str] = None) -> tempfile.TemporaryDirectory:
    """ Get a temp folder object
    :param folder_path: The path to the folder to make (if not provided a temp folder will be created)
    :return: The temp folder path
    """

    if folder_path is None:
        temp_dir = tempfile.TemporaryDirectory()
        logger.info(f"Created Temp folder: {temp_dir.name}")
    else:
        logger.info(f"Use user provided temp folder: {folder_path}")
        # make sure the temp folder exists
        make_folder(folder_path)
        temp_dir = tempfile.TemporaryDirectory(dir=folder_path)
    return temp_dir


def unzip_all_zip_files(input_folder: str, unzip_folder: str) -> None:
    """ Unzip all zip files in a folder
    :param input_folder: The folder containing the zip files
    :param unzip_folder: The folder to unzip the zip files into
    :return: None
    """

    # Make sure the unzip folder exists
    make_folder(unzip_folder)

    # use glob to get a list of all the zip files in the input folder
    zip_files = glob.glob(f"{input_folder}/*.zip")

    # loop thru each zip file
    for zip_file in zip_files:
        # Unzip the file into the unzip folder
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(unzip_folder)
            logger.info(f"Unzipped: {zip_file}")
            for unzip_file in zip_ref.infolist():
                unzip_file_path = os.path.join(unzip_folder, unzip_file.filename)
                unzip_file_modified_datetime = unzip_file.date_time
                # Note the -1 at the end of the tuple is used to handle daylight savings time (DST) for auto-adjusting
                unzip_file_modified_timestamp = time.mktime(unzip_file_modified_datetime + (0, 0, -1))
                # set the access and modified time of the unzipped file to match the zip file
                os.utime(unzip_file_path, (unzip_file_modified_timestamp, unzip_file_modified_timestamp))


def sort_files_by_date(unzip_folder: str, sorted_folder: str) -> None:
    """ Sort files by date
    :param unzip_folder: The folder containing the files to sort
    :param sorted_folder: The folder to sort the files into
    :return: None
    """

    # Make sure the sorted folder exists
    make_folder(sorted_folder)

    # use glob to get a list of all the zip files in the input folder
    files = glob.glob(f"{unzip_folder}/*.*")

    for file in files:
        file_name = os.path.basename(file)
        # Get the last modified date of the file
        modified_time = os.path.getmtime(file)
        modified_date = datetime.fromtimestamp(modified_time)

        # Create a sub folder with the date format in the sorted folder
        date_folder = modified_date.strftime("%m_%d_%Y")
        date_folder_path = os.path.join(sorted_folder, date_folder)

        make_folder(date_folder_path)
        # get filename from path

        move_path = os.path.join(date_folder_path, file_name)
        # Move the file to the corresponding date sub folder
        shutil.move(file, move_path)
        logger.debug(f"Moved: {file} to {move_path}")


def zip_sorted_folders(sorted_folder, output_folder):
    # List all subfolders in the sorted folder
    subfolders = [os.path.join(sorted_folder, d) for d in os.listdir(sorted_folder) if
                  os.path.isdir(os.path.join(sorted_folder, d))]

    for subfolder in subfolders:
        # Get the date from the subfolder name
        date_folder = os.path.basename(subfolder)

        # Create a zip file for each subfolder
        with zipfile.ZipFile(
                os.path.join(output_folder, f"archive_{date_folder}.zip"), 'w', zipfile.ZIP_DEFLATED
        ) as zipf:
            for root, _, files in os.walk(subfolder):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, subfolder)
                    zipf.write(file_path, arcname)

        print(f"Zipped subfolder {date_folder} to archive_{date_folder}.zip")


def main(override_args: Optional[List[str]] = None) -> None:
    """ Main entry point for the script
    :param override_args: A list of arguments to use instead of sys.argv
    :return: None
    """
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description="A command-line argument example")

    # Define command-line arguments
    parser.add_argument(
        '-i',
        '--input',
        type=str,
        help="Input file path that contains the zip files"
    )
    parser.add_argument(
        '-o',
        '--output',
        type=str,
        help="output file path to unzip the zip files into"
    )
    parser.add_argument(
        '-u',
        '--unzip',
        type=str,
        help="temporary path to unzip the zip files into",
        default=None
    )
    parser.add_argument(
        '-s',
        '--sort',
        type=str,
        help="temporary path to sort the zip files into",
        default=None
    )

    # Parse the command-line arguments
    if override_args is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(override_args)

    # Make sure the input folder exists
    if not os.path.exists(args.input):
        logger.error(f"Input folder does not exist: {args.input}")
        sys.exit(1)

    # Make sure the output folder exists
    make_folder(args.output)

    unzip_dir = get_temp_folder(args.unzip)
    sort_dir = get_temp_folder(args.sort)

    # unzip all the zip files into the unzip folder
    logger.info("Unzipping all zip files")
    unzip_all_zip_files(args.input, unzip_dir.name)
    logger.info("Sorting files by date")
    sort_files_by_date(unzip_dir.name, sort_dir.name)

    x = 1
    # if args.temp is not None:
    #     logger.info(f"Cleanup User Provided temp folder: {args.temp}")
    #     os.rmdir(args.temp)


if __name__ == "__main__":
    main(
        override_args=[
            "-i", r"C:\Users\Mike\Downloads\zips",
            "-o", r"C:\Users\Mike\Downloads\output",
            "-u", r"C:\Users\Mike\Downloads\unzip",
            "-s", r"C:\Users\Mike\Downloads\sorted",
        ]
    )
