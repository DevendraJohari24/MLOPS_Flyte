
import typing
from collections import OrderedDict
from dataclasses import dataclass
from typing import Tuple

import joblib
import pandas as pd
from dataclasses_json import dataclass_json
from flytekit import Resources, task, workflow
from flytekit.types.file import FlyteFile
from flytekit.types.schema import FlyteSchema
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
import os
import urllib.request


DATASET_COLUMNS = OrderedDict(
    {
        "#preg": int,
        "pgc_2h": int,
        "diastolic_bp": int,
        "tricep_skin_fold_mm": int,
        "serum_insulin_2h": int,
        "bmi": float,
        "diabetes_pedigree": float,
        "age": int,
        "class": int,
    }
)

FEATURE_COLUMNS = OrderedDict({k: v for k, v in DATASET_COLUMNS.items() if k != "class"})
CLASSES_COLUMNS = OrderedDict({"class": int})


@task(cache_version="1.0", cache=True, limits=Resources(mem="200Mi"))
def split_traintest_dataset(
    dataset: FlyteFile[typing.TypeVar("csv")], seed: int, test_split_ratio: float
) -> Tuple[
    FlyteSchema[FEATURE_COLUMNS],
    FlyteSchema[FEATURE_COLUMNS],
    FlyteSchema[CLASSES_COLUMNS],
    FlyteSchema[CLASSES_COLUMNS],
]:
    column_names = [k for k in DATASET_COLUMNS.keys()]
    df = pd.read_csv(dataset, names=column_names)

    x = df[column_names[:8]]
    y = df[[column_names[-1]]]
    return train_test_split(x, y, test_size=test_split_ratio, random_state=seed)


MODELSER_JOBLIB = typing.TypeVar("joblib.dat")

@dataclass_json
@dataclass
class XGBoostModelHyperparams(object):
    max_depth: int = 3
    learning_rate: float = 0.1
    n_estimators: int = 100
    objective: str = "binary:logistic"
    booster: str = "gbtree"
    n_jobs: int = 1


model_file = typing.NamedTuple("Model", model=FlyteFile[MODELSER_JOBLIB])
workflow_outputs = typing.NamedTuple("WorkflowOutputs", model=FlyteFile[MODELSER_JOBLIB], accuracy=float)


@task(cache_version="1.0", cache=True, limits=Resources(mem="200Mi"))
def fit(
    x: FlyteSchema[FEATURE_COLUMNS],
    y: FlyteSchema[CLASSES_COLUMNS],
    hyperparams: XGBoostModelHyperparams,
) -> model_file:

    x_df = x.open().all()
    y_df = y.open().all()

    m = XGBClassifier(
        n_jobs=hyperparams.n_jobs,
        max_depth=hyperparams.max_depth,
        n_estimators=hyperparams.n_estimators,
        booster=hyperparams.booster,
        objective=hyperparams.objective,
        learning_rate=hyperparams.learning_rate,
    )
    m.fit(x_df, y_df)

    fname = "model.joblib.dat"
    joblib.dump(m, fname)
    return (fname,)


@task(cache_version="1.0", cache=True, limits=Resources(mem="200Mi"))
def predict(
    x: FlyteSchema[FEATURE_COLUMNS],
    model_ser: FlyteFile[MODELSER_JOBLIB],
) -> FlyteSchema[CLASSES_COLUMNS]:

    model = joblib.load(model_ser)
    x_df = x.open().all()
    y_pred = model.predict(x_df)

    col = [k for k in CLASSES_COLUMNS.keys()]
    y_pred_df = pd.DataFrame(y_pred, columns=col, dtype="int64")
    y_pred_df.round(0)
    return y_pred_df


@task(cache_version="1.0", cache=True, limits=Resources(mem="200Mi"))
def score(predictions: FlyteSchema[CLASSES_COLUMNS], y: FlyteSchema[CLASSES_COLUMNS]) -> float:
    pred_df = predictions.open().all()
    y_df = y.open().all()
    acc = accuracy_score(y_df, pred_df)
    print("Accuracy: %.2f%%" % (acc * 100.0))
    return float(acc)



@workflow
def diabetes_xgboost_model(
    dataset: FlyteFile[
        typing.TypeVar("csv")
    ] = "https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv",
    test_split_ratio: float = 0.33,
    seed: int = 7,
) -> workflow_outputs:
    # Task 1
    x_train, x_test, y_train, y_test = split_traintest_dataset( 
        dataset=dataset, seed=seed, test_split_ratio=test_split_ratio
    )
    # Task 2
    model = fit(
        x=x_train,
        y=y_train,
        hyperparams=XGBoostModelHyperparams(max_depth=4),
    )
    # Task 3
    predictions = predict(x=x_test, model_ser=model.model)

    # Task 4
    return model.model, score(predictions=predictions, y=y_test)



if __name__ == "__main__":
    print(f"Running {__file__} main...")
    # download dataset file
    file_name = "pima-indians-diabetes.data.csv"
    urllib.request.urlretrieve("https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv", file_name)
    file_path = os.path.join(os.getcwd(),file_name)
    print(file_path)
    print(diabetes_xgboost_model(dataset=file_path))

