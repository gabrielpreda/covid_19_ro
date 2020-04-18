import pandas as pd
import numpy as np
import os
from content_parser.html_page_parser import HTMLPageParser
from content_parser.regex_parser import get_item

url_base = "https://www.mai.gov.ro/informare-covid-19-grupul-de-comunicare-strategica-"
url_data =\
    [('2020-04-02',"2-aprilie-ora-13-00/"),
     ('2020-04-03',"3-aprilie-2020-ora-13-00/"),
     ('2020-04-04',"4-aprilie-2020-ora-13-00/"),
     ('2020-04-05',"5-aprilie-2020-ora-13-00/"),
     ('2020-04-06',"6-aprilie-2020-ora-13-00/"),
     ('2020-04-07', "6-aprilie-2020-ora-13-00-2/"),
     ('2020-04-08', "8-aprilie-2020-ora-13-00/"),
     ('2020-04-09', "9-aprilie-2020-ora-13-00/"),
     ('2020-04-10', "10-aprilie-2020-ora-13-00/"),
     ('2020-04-11', "11-aprilie-2020-ora-13-00/"),
     ('2020-04-12', "12-aprilie-2020-ora-13-00/"),
     ('2020-04-13', "13-aprilie-2020-ora-13-00/"),
     ('2020-04-14', "14-aprilie-2020-ora-13-00/"),
     ('2020-04-15', "15-aprilie-2020-ora-13-00/"),
     ('2020-04-16', "16-aprilie-2020-ora-13-00/"),
     ('2020-04-17', "16-aprilie-2020-ora-13-00-2/"),
     ('2020-04-18', "18-aprilie-2020-ora-13-00/")
    ]

def get_ati_patients(paragraphs):
    return get_item(paragraphs, "La ATI, în acest moment, sunt internați+(.[0-9]*)")

def get_quarantine(paragraphs):
    return get_item(paragraphs, "în carantină instituționalizată sunt+(.[ 0-9.]*)")
        
def get_isolation(paragraphs):
    return get_item(paragraphs, "de persoane. Alte +(.[ 0-9.]*)")
        
def get_tests(paragraphs):
    return get_item(paragraphs, "Până la această dată, la nivel național, au fost prelucrate+(.[ 0-9.]*)")


def parse_content():        
    hp = HTMLPageParser()
    all_data_df = pd.DataFrame()
    country_data_df = pd.DataFrame()
    for current_date, current_url in url_data:
        compose_url = f"{url_base}{current_url}"
        paragraphs, tables = hp.parse_url(compose_url)

        # Process table data - to extract county-level data
        # retain only the first table
        payload_table = tables[0]
        print(f"current date: {current_date}, table rows: {payload_table.shape[0]}")
        payload_table['date'] = current_date
        #remove headers & footers
        payload_table = payload_table.iloc[1:]
        payload_table = payload_table.iloc[:-1]
        all_data_df = all_data_df.append(payload_table)


        # Process paragraph data - to extract country-level data
        ati = get_ati_patients(paragraphs)
        quarantine = get_quarantine(paragraphs)
        isolation = get_isolation(paragraphs)
        tests = get_tests(paragraphs)  
        country_data_df = country_data_df.append(pd.DataFrame({'date':current_date, 'ati': ati,\
                                        'quarantine': quarantine, 'isolation': isolation, 'tests': tests}, index=[0]))
    
    all_data_df.columns = ['No', 'County', 'Confirmed', 'Date']
    return all_data_df, country_data_df


def check_number_of_counties(all_data_df):    
    COUNTY_NUMBER = 42
    try:
        assert (len(all_data_df.County.unique())== (COUNTY_NUMBER + 1)), "wrong County number"
    except Exception as ex:
        print(f"Error: {ex}")

        
def data_cleaning(all_data_df, country_data_df):
    
    all_data_df.loc[all_data_df['County']=='–', 'County'] = 'Not identified'    

    # replace - in Confirmed
    all_data_df.loc[all_data_df['Confirmed']=='–', 'Confirmed'] = 0
    # fix decimal point
    all_data_df['Confirmed'] = all_data_df['Confirmed'].astype(str)
    all_data_df['Confirmed'] = all_data_df['Confirmed'].apply(lambda x: x.replace(".", ""))
    all_data_df['Confirmed'] = all_data_df['Confirmed'].astype(int)

    # fix decimal point
    country_data_df.loc[country_data_df['quarantine']==' ', 'quarantine'] = 0
    for feature in ['ati', 'quarantine', 'isolation', 'tests']:
        country_data_df[feature] = country_data_df[feature].astype(str)
        country_data_df[feature] = country_data_df[feature].apply(lambda x: x.replace(".", ""))
        country_data_df[feature] = country_data_df[feature].astype(int)

    return all_data_df, country_data_df

        
def save_data(all_data_df, country_data_df):
    for date in all_data_df.Date.unique():
        d_df = all_data_df.loc[all_data_df.Date==date]
        d_df.to_csv(os.path.join('ro_covid_19_daily_reports', f"{date}.csv"), index=False)    

    all_data_df.to_csv(os.path.join('ro_covid_19_time_series', "ro_covid_19_time_series.csv"), index=False)
    country_data_df.to_csv(os.path.join('ro_covid_19_time_series', "ro_covid_19_country_data_time_series.csv"), index=False)

def check_data(all_data_df):    
    all_data_df.groupby('Date')['Confirmed'].sum()
    
    
def main():
    all_data_df, country_data_df = parse_content()
    check_number_of_counties(all_data_df)
    all_data_df, country_data_df = data_cleaning(all_data_df, country_data_df)
    check_data(all_data_df)
    save_data(all_data_df, country_data_df)
    
if __name__ == "__main__":
    main()

    
    