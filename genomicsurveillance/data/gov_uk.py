import pandas as pd
from uk_covid19 import Cov19API

from genomicsurveillance.config import GovUKAPI

from .meta_data import get_meta_data


def get_specimen(ltla_list: list = None):
    """
    Downloads the newest specimen data (newCasesBySpecimenDate) from the
    GOV UK Covid-19 api. Returns a (LTLA x dates) table.
    """
    if ltla_list is None:
        ltla_list = get_meta_data().lad19cd.tolist()

    specimen_dfs = get_ltla_data(ltla_list)
    specimen = extract_covariate(specimen_dfs, "newCasesBySpecimenDate")
    return specimen


def extract_covariate(dataframes, covariate="newCasesByPublishDate"):
    filtered = pd.concat(
        [
            current_df.drop_duplicates()
            # .assign(date=lambda df: pd.DatetimeIndex(df.date))
            .sort_values(by="date")
            .reset_index(drop=True)
            .loc[:, ["date", "areaCode", covariate]]
            for current_df in dataframes
        ]
    ).reset_index(drop=True)

    pivot = (
        filtered.pivot_table(
            index="date", columns="areaCode", values=covariate, dropna=False
        )
        .reset_index()
        .rename_axis(None, axis=1)
        .set_index("date")
    )

    return pivot


def get_ltla_data(
    ltla_list: list, structure: dict = GovUKAPI.specimen, max_retry: int = 3
):
    dataframes = []
    for i, ltla in enumerate(ltla_list):
        # print(f"{ltla['lad19nm']}")
        retry = 1
        failure = False
        while not failure:
            try:
                api = Cov19API(filters=[f"areaCode={ltla}"], structure=structure)
                df = api.get_dataframe()
                break
            except Exception:
                print(
                    f"Failed downloading areaCode={ltla} ... retrying {retry}/{max_retry}."
                )
                retry += 1

            finally:
                if retry == max_retry:
                    failure = True

        if df.shape == (0, 0) or failure:
            continue
        dataframes.append(df)

    return dataframes
