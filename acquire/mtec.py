import requests
import polars as pl
from bs4 import BeautifulSoup

from acquire.assimilate import assimilate_raw_results
from dao import RawResults


def _attach_gender_place(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        pl.col('SexPl').str.split('/')[0].cast(pl.Int64).alias('gender_place')
    )


def scrape_race(race_id: int) -> RawResults:
    res = requests.get('https://www.mtecresults.com/race/quickResults',
                            # who knows what max perPage the server will allow, but 500 should be good for most races
                            params={'raceid': str(race_id), 'version': '31', 'overall': 'yes', 'perPage': '500'},
                            headers={'X-Requested-With': 'XMLHttpRequest'})
    soup = BeautifulSoup(res.text, 'html.parser')

    header = [cell.text for cell in soup.select('.runnersearch-header-cell')]
    rows = [[cell.text for cell in row.select('.runnersearch-cell')] for row in soup.select('.runnersearch-row')]

    data = {col: [row[i] for row in rows] for i, col in enumerate(header)}
    data['raw_result_id'] = range(1, len(rows) + 1)
    rr = _attach_gender_place(pl.DataFrame(data)).rename({
        'Name': 'name',
        'Sex': 'gender',
        'Age': 'age',
        'City': 'location',
        'Time': 'time',
    }).select(pl.col('raw_result_id'), pl.col('name'), pl.col('gender'), pl.col('age'), pl.col('location'), pl.col('time'), pl.col('gender_place'))

    return assimilate_raw_results(rr)
