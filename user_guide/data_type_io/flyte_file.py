import csv
import os
from collections import defaultdict
from typing import List

import flytekit
from flytekit import task, workflow
from flytekit.types.file import FlyteFile

@task
def normalize_columns(
    csv_url: FlyteFile,
    column_names: List[str],
    columns_to_normalize: List[str],
    output_location: str,
) -> FlyteFile:
    # read the data from the raw csv file
    parsed_data = defaultdict(list)
    with open(csv_url, newline="\n") as input_file:
        reader = csv.DictReader(input_file, fieldnames=column_names)
        next(reader)  # Skip header
        for row in reader:
            for column in columns_to_normalize:
                parsed_data[column].append(float(row[column].strip()))

    # normalize the data
    normalized_data = defaultdict(list)
    for colname, values in parsed_data.items():
        mean = sum(values) / len(values)
        std = (sum([(x - mean) ** 2 for x in values]) / len(values)) ** 0.5
        normalized_data[colname] = [(x - mean) / std for x in values]

    # write to local path
    out_path = os.path.join(
        flytekit.current_context().working_directory,
        f"normalized-{os.path.basename(csv_url.path).rsplit('.')[0]}.csv",
    )
    with open(out_path, mode="w") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=columns_to_normalize)
        writer.writeheader()
        for row in zip(*normalized_data.values()):
            writer.writerow({k: row[i] for i, k in enumerate(columns_to_normalize)})

    if output_location:
        return FlyteFile(path=out_path, remote_path=output_location)
    else:
        return FlyteFile(path=out_path)



@workflow
def normalize_csv_file(
    csv_url: FlyteFile,
    column_names: List[str],
    columns_to_normalize: List[str],
    output_location: str = "",
) -> FlyteFile:
    return normalize_columns(
        csv_url=csv_url,
        column_names=column_names,
        columns_to_normalize=columns_to_normalize,
        output_location=output_location,
    )

if __name__ == "__main__":
    default_files = [
        (
            "biostats.csv",
            ["Name", "Sex", "Age", "Heights (in)", "Weight (lbs)"],
            ["Age"],
        ),
        (
            "faithful.csv",
            ["Index", "Eruption length (mins)", "Eruption wait (mins)"],
            ["Eruption length (mins)"],
        ),
    ]
    print(f"Running {__file__} main...")
    for index, (csv_url, column_names, columns_to_normalize) in enumerate(default_files):
        normalized_columns = normalize_csv_file(
            csv_url=csv_url,
            column_names=column_names,
            columns_to_normalize=columns_to_normalize,
        )
        print(f"Running normalize_csv_file workflow on {csv_url}: " f"{normalized_columns}")



# pyflyte run --remote --image=registry.accounts.intern/joharide/flyte_diabetes:fourth flyte_file.py  normalize_csv_file --csv_url="https://people.sc.fsu.edu/~jburkardt/data/csv/biostats.csv" --column_names='["Name", "Sex", "Age", "Heights (in)", "Weight (lbs)"]' --columns_to_normalize='["Age"]'