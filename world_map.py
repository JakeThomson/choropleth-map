from plotly import graph_objs as go
import pandas as pd
import requests
import bs4 as bs
import pprint as pp


def update_csv():
    resp = requests.get("https://www.worldometers.info/coronavirus/")
    soup = bs.BeautifulSoup(resp.text, "lxml")
    table_rows = soup.findAll("table")[0].findAll("tr")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}

    temp_df = pd.read_csv('world_codes.csv', index_col="CODE", engine="python")

    for i, row in enumerate(table_rows[1:len(table_rows) - 1]):
        if i == 0:
            continue
        table_cells = table_rows[i].findAll("td")
        country = table_cells[0].next
        cases = table_cells[1].next
        cases = int(cases.replace(",", ""))

        if country == " ":
            continue
        elif country == " USA ":
            temp_df.loc["USA", "CASES"] = cases
        elif country == " Bhutan ":
            temp_df.loc["BTN", "CASES"] = cases
        elif country == " Costa Rica ":
            temp_df.loc["CRI", "CASES"] = cases
        else:
            print(f"Grabbing {str(country)} with {cases} cases ISO code")
            while True:
                try:
                    google_resp = requests.get(f"https://www.google.com/search?q={country}+ISO+code", headers=headers)
                    google_soup = bs.BeautifulSoup(google_resp.text, 'html.parser')

                    code = google_soup.find("div", {"class": "Z0LcW"}).next
                    print(code)

                    temp_df.loc[code, "CASES"] = cases
                    break
                except ValueError as e:
                    print(f"Error: {e}")
                    break
                except requests.exceptions.ConnectionError:
                    print(f"Error: {e}")
                    print("Retrying...")

    temp_df.to_csv("world_codes.csv")


df = pd.read_csv('world_codes.csv')
for col in df.columns:
    df[col] = df[col].astype(str)

df["text"] = df["COUNTRY"] + "<br>" + \
             "Cases: " + df["CASES"]

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
