import math
from datetime import time

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

        active = cases - deaths - recoveries

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
            old_active = temp_df.loc[code, "ACTIVE"]
            if isinstance(old_cases, str):
                old_cases = int((temp_df.loc[code, "CASES"]).replace(",", ""))
            if isinstance(old_deaths, str):
                old_deaths = int((temp_df.loc[code, "DEATHS"]).replace(",", ""))
            if isinstance(old_recoveries, str):
                old_recoveries = int((temp_df.loc[code, "RECOVERIES"]).replace(",", ""))
            if isinstance(old_active, str):
                old_active = int((temp_df.loc[code, "ACTIVE"]).replace(",", ""))

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

            if active - old_active == 0:
                temp_df.loc[code, "NEW ACTIVE"] = " "
            elif active - old_active > 0:
                temp_df.loc[code, "NEW ACTIVE"] = " (+" + format(active - old_active, ",") + ")"
            else:
                temp_df.loc[code, "NEW ACTIVE"] = " (" + format(active - old_active, ",") + ")"

            temp_df.loc[code, "CASES"] = format(cases, ",")
            temp_df.loc[code, "DEATHS"] = format(deaths, ",")
            temp_df.loc[code, "RECOVERIES"] = format(recoveries, ",")
            temp_df.loc[code, "ACTIVE"] = format(active, ",")
            if not active == 0:
                temp_df.loc[code, "ACTIVE LOG"] = math.log(active)
            if not cases == 0:
                temp_df.loc[code, "MORTALITY RATE"] = str(round(deaths/cases*100, 2)) + "%"
            else:
                temp_df.loc[code, "MORTALITY RATE"] = "0"
            temp_df.loc[code, "LOGS"] = math.log(cases)
        except KeyError as e:
            pass

    temp_df.to_csv("world_data.csv")


df = pd.read_csv('world_data.csv')

for col in df.columns:
    df[col] = df[col].astype(str)

df["text"] = df["COUNTRY"] + "<br>" + \
             "Total Cases: " + df["CASES"] + df["NEW CASES"] + "<br>" + \
             "Total Deaths: " + df["DEATHS"] + df["NEW DEATHS"] + "<br>" + \
             "Total Recoveries: " + df["RECOVERIES"] + df["NEW RECOVERIES"] + "<br>" + \
             "Mortality Rate: " + df["MORTALITY RATE"]

df["text2"] = df["COUNTRY"] + "<br>" + \
             "Active Cases: " + df["ACTIVE"] + df["NEW ACTIVE"] + "<br>" + \
             "Total Deaths: " + df["DEATHS"] + df["NEW DEATHS"] + "<br>" + \
             "Total Recoveries: " + df["RECOVERIES"] + df["NEW RECOVERIES"] + "<br>" + \
             "Mortality Rate: " + df["MORTALITY RATE"]


def create_fig(z, text, color, title):
    return go.Figure(data=go.Choropleth(
        locations=df['CODE'],
        z=df[z],
        text=df[text],
        colorscale=color,
        autocolorscale=False,
        reversescale=False,
        marker_line_color='darkgray',
        marker_line_width=0.5,
        colorbar_title=title,
    ))


def update_fig(fig, title):
    fig.update_layout(
        title_text=title,
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


if len(sys.argv) > 1 and sys.argv[1].lower() == "update":
    update_csv()
    fig = create_fig("LOGS", "text", "reds", "Total cases (log(x))")
    update_fig(fig, "Total COVID-19 cases")
    fig.show()

elif sys.argv[1].lower() == "active":
    fig = create_fig("ACTIVE LOG", "text2", "greens", "Active cases (log(x))")
    update_fig(fig, "Active COVID-19 cases")
    fig.show()
