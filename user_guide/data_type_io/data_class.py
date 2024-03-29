import os
import tempfile
from dataclasses import dataclass

import pandas as pd
from flytekit import task, workflow
from flytekit.types.directory import FlyteDirectory
from flytekit.types.file import FlyteFile
from flytekit.types.structured import StructuredDataset
from mashumaro.mixins.json import DataClassJSONMixin


@dataclass
class Datum(DataClassJSONMixin):
    x: int
    y: str
    z: dict[int, str]


@task
def stringify(s: int) -> Datum:
    """
    A dataclass return will be treated as a single complex JSON return.
    """
    return Datum(x=s, y=str(s), z={s: str(s)})


@task
def add(x: Datum, y: Datum) -> Datum:
    """
    Flytekit automatically converts the provided JSON into a data class.
    If the structures don't match, it triggers a runtime failure.
    """
    x.z.update(y.z)
    return Datum(x=x.x + y.x, y=x.y + y.y, z=x.z)



@dataclass
class FlyteTypes(DataClassJSONMixin):
    dataframe: StructuredDataset
    file: FlyteFile
    directory: FlyteDirectory


@task
def upload_data() -> FlyteTypes:
    # 1. StructuredDataset
    df = pd.DataFrame({"Name": ["Tom", "Joseph"], "Age": [20, 22]})

    # 2. FlyteDirectory
    temp_dir = tempfile.mkdtemp(prefix="flyte-")
    df.to_parquet(temp_dir + "/df.parquet")

    # 3. FlyteFile
    file_path = tempfile.NamedTemporaryFile(delete=False)
    file_path.write(b"Hello, World!")

    fs = FlyteTypes(
        dataframe=StructuredDataset(dataframe=df),
        file=FlyteFile(file_path.name),
        directory=FlyteDirectory(temp_dir),
    )
    return fs


@task
def download_data(res: FlyteTypes):
    assert pd.DataFrame({"Name": ["Tom", "Joseph"], "Age": [20, 22]}).equals(res.dataframe.open(pd.DataFrame).all())
    f = open(res.file, "r")
    assert f.read() == "Hello, World!"
    assert os.listdir(res.directory) == ["df.parquet"]


@workflow
def dataclass_wf(x: int, y: int) -> (Datum, FlyteTypes):
    o1 = add(x=stringify(s=x), y=stringify(s=y))
    o2 = upload_data()
    download_data(res=o2)
    return o1, o2

