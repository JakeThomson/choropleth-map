import math
import pycountry
from plotly import graph_objs as go
import pandas as pd
import requests
import bs4 as bs
import sys


def update_csv():
    resp = requests.get("https://www.worldometers.info/coronavirus/")
    soup = bs.BeautifulSoup(resp.text, "lxml")
    table_rows = soup.findAll("table")[0].findAll("tr")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}

    temp_df = pd.read_csv('world_codes.csv', index_col="CODE", engine="python")
    codes = pd.read_csv("country_codes.csv", index_col="COUNTRY")

    for i, row in enumerate(table_rows[1:len(table_rows) - 1]):
        if i == 0:
            continue
        table_cells = table_rows[i].findAll("td")
        country = table_cells[0].next.strip()
        country = country.replace("St.", "Saint")
        country = country.replace("N.", "North")
        country = country.replace("S.", "South")

        cases = table_cells[1].next
        cases = int(cases.replace(",", ""))

        if country == "":
            continue
        else:
            if country in codes.index:
                code = codes.loc[country, "CODE"]
            else:
                print(f"{str(country)} ({cases} cases) is not in country_codes.csv, grabbing ISO code from google")
                while True:
                    try:
                        code = pycountry.countries.search_fuzzy(country)
                        break
                    except ValueError:
                        break
                    except requests.exceptions.ConnectionError:
                        print(f"Error: {e}")
                        print("Retrying...")

        try:
            if cases - temp_df.loc[code, "CASES"] == 0:
                temp_df.loc[code, "NEW CASES"] = " "
            else:
                temp_df.loc[code, "NEW CASES"] = " (+" + str(cases - temp_df.loc[code, "CASES"]) + ")"

            if temp_df.loc[code, "NEW CASES"] == 0:
                temp_df.loc[code, "NEW CASES"] = " "

            temp_df.loc[code, "CASES"] = cases
            temp_df.loc[code, "LOGS"] = math.log(cases)
        except KeyError as e:
            print(f"Error: {e}")

    temp_df.to_csv("world_codes.csv")


update_csv()

if len(sys.argv) > 1 and sys.argv[1] == "update":
    update_csv()

df = pd.read_csv('world_codes.csv')
for col in df.columns:
    df[col] = df[col].astype(str)

df["text"] = df["COUNTRY"] + "<br>" + \
             "Total Cases: " + df["CASES"] + df["NEW CASES"]

fig = go.Figure(data=go.Choropleth(
    locations=df['CODE'],
    z=df['LOGS'],
    text=df['text'],
    colorscale="reds",
    autocolorscale=False,
    reversescale=False,
    marker_line_color='darkgray',
    marker_line_width=0.5,
    colorbar_title='Active Cases',
))

fig.update_layout(
    title_text='Coronavirus cases',
    geo=dict(
        showframe=False,
        showcoastlines=False,
        projection_type='equirectangular',
        showlakes=False
    ),
    annotations=[dict(
        x=0.55,
        y=0.1,
        xref='paper',
        yref='paper',
        text='',
        showarrow=False
    )]
)

fig.show()
