import csv
import os
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import List

import flytekit
from flytekit import task, workflow
from flytekit.types.directory import FlyteDirectory

@task
def download_files(csv_urls: List[str]) -> FlyteDirectory:
    working_dir = flytekit.current_context().working_directory
    local_dir = Path(os.path.join(working_dir, "csv_files"))
    local_dir.mkdir(exist_ok=True)

    # get the number of digits needed to preserve the order of files in the local directory
    zfill_len = len(str(len(csv_urls)))
    for idx, remote_location in enumerate(csv_urls):
        local_image = os.path.join(
            # prefix the file name with the index location of the file in the original csv_urls list
            local_dir,
            f"{str(idx).zfill(zfill_len)}_{os.path.basename(remote_location)}",
        )
        urllib.request.urlretrieve(remote_location, local_image)
    return FlyteDirectory(path=str(local_dir))


def normalize_columns(
    local_csv_file: str,
    column_names: List[str],
    columns_to_normalize: List[str],
):
    # read the data from the raw csv file
    parsed_data = defaultdict(list)
    with open(local_csv_file, newline="\n") as input_file:
        reader = csv.DictReader(input_file, fieldnames=column_names)
        for row in (x for i, x in enumerate(reader) if i > 0):
            for column in columns_to_normalize:
                parsed_data[column].append(float(row[column].strip()))

    # normalize the data
    normalized_data = defaultdict(list)
    for colname, values in parsed_data.items():
        mean = sum(values) / len(values)
        std = (sum([(x - mean) ** 2 for x in values]) / len(values)) ** 0.5
        normalized_data[colname] = [(x - mean) / std for x in values]

    # overwrite the csv file with the normalized columns
    with open(local_csv_file, mode="w") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=columns_to_normalize)
        writer.writeheader()
        for row in zip(*normalized_data.values()):
            writer.writerow({k: row[i] for i, k in enumerate(columns_to_normalize)})


@task
def normalize_all_files(
    csv_files_dir: FlyteDirectory,
    columns_metadata: List[List[str]],
    columns_to_normalize_metadata: List[List[str]],
) -> FlyteDirectory:
    for local_csv_file, column_names, columns_to_normalize in zip(
        # make sure we sort the files in the directory to preserve the original order of the csv urls
        [os.path.join(csv_files_dir, x) for x in sorted(os.listdir(csv_files_dir))],
        columns_metadata,
        columns_to_normalize_metadata,
    ):
        normalize_columns(local_csv_file, column_names, columns_to_normalize)
    return FlyteDirectory(path=csv_files_dir.path)


@workflow
def download_and_normalize_csv_files(
    csv_urls: List[str],
    columns_metadata: List[List[str]],
    columns_to_normalize_metadata: List[List[str]],
) -> FlyteDirectory:
    directory = download_files(csv_urls=csv_urls)
    return normalize_all_files(
        csv_files_dir=directory,
        columns_metadata=columns_metadata,
        columns_to_normalize_metadata=columns_to_normalize_metadata,
    )