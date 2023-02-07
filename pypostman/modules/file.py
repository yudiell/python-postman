import os
import platform
import gzip
import boto3
import pytz
import tempfile
import glob

from pathlib import PurePath
from zipfile import ZipFile
from typing import Iterator
from datetime import datetime
from .logger import Log


class File:
    def __init__(self) -> None:
        self.log = Log()
        self.tempdir = tempfile.TemporaryDirectory()
        self.current_os = platform.system()

    def unzip(self, file: str, path: str, extn: str) -> list:
        """
        param: file: str -> The file to be unzipped.
        param: path: str -> The path where the unzipped file will be written to.
        param: extn: str -> The unzipped file extension. Ex: csv, json

        Returns a file(s) list that match the extn param.
        """
        self.log.info(f"Unzipping file: {file}")
        with ZipFile(file=file, mode="r") as zipfile:
            zipfile.extractall(path=path)
            files = glob.glob(f"{path}/*.{extn}")
            self.log.info(f"File(s) unzipped: {files}")
            return files

    def compress(self, file: str) -> str:
        """
        gzip the imput temp file.
        returns the filename.
        """
        if self.current_os == "Windows":
            with gzip.open(f"{file}.gz", "wb") as compressed:
                chunks = self.read_file_in_chunks(file=file, n=10000)
                for chunk in chunks:
                    compressed.write(chunk)
                self.log.info(f"{file} Compressed.")
                return compressed.name
        else:
            self.log.info(f"Compressing file {file}...")
            os.system(f"gzip {file}")
            self.log.info(f"{file} compressed successfully.")
            return f"{file}.gz"

    def write(self, payload: Iterator, filename: str) -> str:
        """
        : param payload: Any response payload, csv, json, zip, gzip.
        : param filename: Any preferred filename, ex. myFile.csv. (Will be written to a temporary)
        Returns the temporary directory path + filename.
        The temprary directory will be garbage collected if the File object is disposed or due to an exception.
        """
        tempfile = "".join([self.tempdir.name, "/", filename])
        tempfile = PurePath(tempfile)
        self.log.info(f"Writing to: {tempfile}...")
        with open(file=tempfile, mode="wb") as file:
            payload_size = 0
            total_size = 0
            for chunk in payload:
                payload_size += payload.__sizeof__()
                total_size += len(chunk)
                file.write(chunk)
        self.log.info(f"Write to file completed.")
        return tempfile

    def s3_upload(self, filepath: str, bucket: str, key: str) -> None:
        """
        Upload a file to S3.
        :param filepath: The source file path.
        :param bucket: The s3 target bucket name.
        :param key: The s3 object name. (File name in s3, ex. /dev/business_unit/dataset/subdataset/daily/date/filename.json.gz)
        """
        self.log.info(f"Uploading file to S3...")
        self.log.info(f"Source: {filepath}")
        self.log.info(f"Target: {key}")
        client = boto3.client("s3")
        client.upload_file(Filename=filepath, Bucket=bucket, Key=key)
        self.log.info(f"File uploaded successfully to: {key}")

    def list_objects(self, bucket: str, prefix: str) -> list:
        """
        List objects from the bucket.
        :param bucket: Name of the bucket
        :type bucket: str
        :param prefix: The key prefix
        :type prefix: str
        :return: Metadata for all objects from the bucket
        :rtype: collections.Iterable[dict[str, any]]
        """
        client = boto3.client("s3")
        # Use paginator abstraction to seamlessly iterate over pages.
        # list_objects_v2 provides maximum 1000 objects per request, pagination
        # is used in AWS sdk in order to split large collections into several
        # smaller, limited requests)
        paginator = client.get_paginator("list_objects_v2")
        page = 1

        for result in paginator.paginate(
            Bucket=bucket, Prefix=prefix, RequestPayer="requester"
        ):
            self.log.info("\tReading page {}.".format(page))
            page += 1

            for item in result.get("Contents", []):
                yield item

    def s3_delete(
        self, bucket: str, prefix: str, last_modified: datetime, max_count: int = 20
    ) -> bool:
        """
        Delete a file from an S3 bucket
        ***** Please verify that the prefix parameter is correct... Objects are permanetnly deleted. *****
        :param bucket, Bucket to delete from
        :param prefix, filter to be passed to the s3 bucket it selects the objects that match the prefix. Ex: dev/musket_systems/kpler/trades/cpp
        :param last_modified, Select files oder than the timestamp passed.
            The filter targets the s3 object's last modified date. Ex: last_modified = datetime.now() - timedelta(days=31).
            Uses last_modified.replace(tzinfo=pytz.UTC)
        :param max_count (not required, default = 20), pass a value if you need more than 20 objects deleted.
        Returns True if objects were deleted, else False
        Logs the s3 response.
        """
        # self.log.info('Deleting files from S3.')
        last_modified = last_modified.replace(tzinfo=pytz.UTC)
        self.log.info(f"Bucket: {bucket}")
        self.log.info(f"Prefix: {prefix}")
        self.log.info(f"Last modified: {last_modified}")
        self.log.info(f"Max count: {max_count}")
        # Deleted files
        client = boto3.client("s3")
        bucket = bucket

        content = self.list_objects(bucket=bucket, prefix=prefix)

        if content:
            delete = {}
            delete["Objects"] = [
                {"Key": item["Key"]}
                for item in content
                if item["LastModified"] < last_modified
            ]

            delete_count = len(delete["Objects"])
            if delete_count != 0:
                assert delete_count <= max_count, self.log.error(
                    f"""Delete count: {delete_count}\r\nThere are too many objects to delete, please verify that the prefix is correct. Max count = {max_count}
                ----> Objects available for deletion [{delete_count}]."""
                )
                self.log.info(f"Deleting objects with prefix: {prefix}")
                delete_response = client.delete_objects(Bucket=bucket, Delete=delete)
                self.log.info(delete_response)
                return True
            else:
                self.log.info(
                    f"No objects met the last modified condition {last_modified}"
                )
                return False
        else:
            self.log.info(f"No objects met the prefix condition {prefix}")
            return False

    def get_file_extension(self, content_type: str) -> str:
        """
        This function takes in a content type as an argument and returns the corresponding file extension as a string.
        If no corresponding file extension exists, it returns '.bin' as the file extension.
        """
        self.log.info(f"API response content type: {content_type}")
        extensions = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/bmp": ".bmp",
            "audio/mp3": ".mp3",
            "audio/wav": ".wav",
            "audio/aac": ".aac",
            "video/mp4": ".mp4",
            "video/avi": ".avi",
            "video/mkv": ".mkv",
            "text/html": ".html",
            "text/plain": ".txt",
            "text/javascript": ".js",
            "application/pdf": ".pdf",
            "application/json": ".json",
            "application/xml": ".xml",
            "application/csv": ".csv",
            "application/x-zip-compressed": ".zip",
        }
        ext: str = None
        for extension in extensions:
            if extension in content_type:
                ext = extensions[extension]

        if ext:
            return ext
        return ".bin"
