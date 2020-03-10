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

    temp_df = pd.read_csv('world_data.csv', index_col="CODE", engine="python")
    codes = pd.read_csv("country_codes.csv", index_col="COUNTRY")

    for i, row in enumerate(table_rows[1:len(table_rows) - 1]):
        if i == 0:
            continue
        table_cells = table_rows[i].findAll("td")
        country = table_cells[0].next.strip()
        if country == "":
            try:
                country = table_cells[0].findAll("a")[0].next
            except IndexError:
                print("Do one Diamond Princess.")

        country = country.replace("St.", "Saint")
        country = country.replace("N.", "North")
        country = country.replace("S.", "South")

        cases = table_cells[1].next
        cases = int(cases.replace(",", ""))

        deaths = table_cells[3].next
        if not deaths == " ":
            deaths = int(deaths.replace(",", ""))
        else:
            deaths = 0

        recoveries = table_cells[5].next
        if not recoveries == " ":
            recoveries = int(recoveries.replace(",", ""))
        else:
            recoveries = 0

        if country == "" or country == "Channel Islands":
            continue
        else:
            if country in codes.index:
                code = codes.loc[country, "CODE"]
            else:
                print(f"{str(country)} ({cases} cases) is not in country_codes.csv, grabbing ISO code from google")
                while True:
                    try:
                        code = pycountry.countries.search_fuzzy(country)[0].alpha_3
                        codes.loc[country, "CODE"] = code
                        codes.to_csv("country_codes.csv")
                        break
                    except ValueError:
                        break
                    except requests.exceptions.ConnectionError:
                        print(f"Error: {e}")
                        print("Retrying...")

        try:
            old_cases = temp_df.loc[code, "CASES"]
            old_deaths = temp_df.loc[code, "DEATHS"]
            old_recoveries = temp_df.loc[code, "RECOVERIES"]
            if isinstance(old_cases, str):
                old_cases = int((temp_df.loc[code, "CASES"]).replace(",", ""))
            if isinstance(old_deaths, str):
                old_deaths = int((temp_df.loc[code, "DEATHS"]).replace(",", ""))
            if isinstance(old_recoveries, str):
                old_recoveries = int((temp_df.loc[code, "RECOVERIES"]).replace(",", ""))

            if cases - old_cases == 0:
                temp_df.loc[code, "NEW CASES"] = " "
            else:
                temp_df.loc[code, "NEW CASES"] = " (+" + format(cases - old_cases, ",") + ")"

            if deaths - old_deaths == 0:
                temp_df.loc[code, "NEW DEATHS"] = " "
            else:
                temp_df.loc[code, "NEW DEATHS"] = " (+" + format(deaths - old_deaths, ",") + ")"

            if recoveries - old_recoveries == 0:
                temp_df.loc[code, "NEW RECOVERIES"] = " "
            else:
                temp_df.loc[code, "NEW RECOVERIES"] = " (+" + format(recoveries - old_recoveries, ",") + ")"

            temp_df.loc[code, "CASES"] = format(cases, ",")
            temp_df.loc[code, "DEATHS"] = format(deaths, ",")
            temp_df.loc[code, "RECOVERIES"] = format(recoveries, ",")
            temp_df.loc[code, "LOGS"] = math.log(cases)
        except KeyError as e:
            pass

    temp_df.to_csv("world_data.csv")


if len(sys.argv) > 1 and sys.argv[1] == "update":
    update_csv()

df = pd.read_csv('world_data.csv')
for col in df.columns:
    df[col] = df[col].astype(str)

df["text"] = df["COUNTRY"] + "<br>" + \
             "Total Cases: " + df["CASES"] + df["NEW CASES"] + "<br>" + \
             "Total Deaths: " + df["DEATHS"] + df["NEW DEATHS"] + "<br>" + \
             "Total Recoveries: " + df["RECOVERIES"] + df["NEW RECOVERIES"]

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
