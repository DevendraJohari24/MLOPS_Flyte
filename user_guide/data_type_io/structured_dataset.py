import os
import typing

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from flytekit import FlyteContext, StructuredDatasetType, kwtypes, task, workflow
from flytekit.models import literals
from flytekit.models.literals import StructuredDatasetMetadata
from flytekit.types.structured.structured_dataset import (
    PARQUET,
    StructuredDataset,
    StructuredDatasetDecoder,
    StructuredDatasetEncoder,
    StructuredDatasetTransformerEngine,
)
from typing_extensions import Annotated




@task
def generate_pandas_df(a: int) -> pd.DataFrame:
    return pd.DataFrame({"Name": ["Tom", "Joseph"], "Age": [a, 22], "Height": [160, 178]})


all_cols = kwtypes(Name=str, Age=int, Height=int)
col = kwtypes(Age=int)


@task
def get_subset_pandas_df(df: Annotated[StructuredDataset, all_cols]) -> Annotated[StructuredDataset, col]:
    df = df.open(pd.DataFrame).all()
    df = pd.concat([df, pd.DataFrame([[30]], columns=["Age"])])
    return StructuredDataset(dataframe=df)



@workflow
def simple_sd_wf(a: int = 19) -> Annotated[StructuredDataset, col]:
    pandas_df = generate_pandas_df(a=a)
    return get_subset_pandas_df(df=pandas_df)