import pandas as pd
import numpy as np
import os
from content_parser.html_page_parser import HTMLPageParser
from content_parser.regex_parser import get_item


def get_ati_patients(paragraphs):
    return get_item(paragraphs, "La ATI, în acest moment, sunt internați+(.[0-9]*)")

def get_quarantine(paragraphs):
    return get_item(paragraphs, "în carantină instituționalizată sunt+(.[ 0-9.]*)")
        
def get_isolation(paragraphs):
    return get_item(paragraphs, "persoane. Alte +(.[ 0-9.]*)")
        
def get_tests(paragraphs):
    return get_item(paragraphs, "Până la această dată, la nivel național, au fost prelucrate+(.[ 0-9.]*)")

def compose_current_date_url(crt_day):
    url_base = "https://www.mai.gov.ro/informare-covid-19-grupul-de-comunicare-strategica-"
    months = ['ianuarie', 'februarie', 'martie', 'aprilie', 'mai', 'iunie',
          'iulie', 'august', 'septembrie', 'octombrie', 'noiembrie', 'decembrie']

    current_date = '%d-%02d-%02d' % (crt_day.year, crt_day.month, crt_day.day)
    current_url = '%d-%s-%d-ora-13-00/' % (crt_day.day, months[crt_day.month - 1], crt_day.year)

    # exception treatment
    if(current_date == "2020-04-02"):
        current_url = '%d-%s-ora-13-00/' % (crt_day.day, months[crt_day.month  - 1])
    if(current_date in ["2020-04-07", "2020-04-17"]):
        current_url = '%d-%s-%d-ora-13-00-2/' % (crt_day.day - 1, months[crt_day.month - 1], crt_day.year)
    
    composed_url = f"{url_base}{current_url}"
    
    if(current_date == "2020-05-01"):
        composed_url = "https://www.mai.gov.ro/21331-2/"    

    return current_date, composed_url

def parse_content():        
    hp = HTMLPageParser()
    all_data_df = pd.DataFrame()
    country_data_df = pd.DataFrame()

    crt_day = dt.datetime.strptime("2020-04-02", "%Y-%m-%d")
    end_day = dt.datetime.now()
    delta = dt.timedelta(days=1)
    while crt_day <= end_day:
        crt_day += delta
        current_date, composed_url = compose_current_date_url(crt_day)
        paragraphs, tables = hp.parse_url(composed_url)

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
    """
    check that the number of counties in Romania is 42
    """
    COUNTY_NUMBER = 42
    try:
        assert (len(all_data_df.County.unique())== (COUNTY_NUMBER + 1)), "wrong County number"
        print("County number valid")
    except Exception as ex:
        print(f"Error: {ex}")

def fix_decimal(data):
    """
    @param data - the data to have removed the decimal point
    Data is as well converted to int
    @return the cleaned int data
    """
    data = str(data)
    data = data.replace(".", "")
    try:
        data = int(data)
    except:
        data = 0
        
    return data
    
        
def data_cleaning(all_data_df, country_data_df):
    
    # replace '-' with not identified County data
    all_data_df.loc[all_data_df['County']=='–', 'County'] = 'Not identified'    

    # replace decimal point in Confirmed
    all_data_df.loc[all_data_df['Confirmed']=='–', 'Confirmed'] = 0
    # fix decimal point
    all_data_df['Confirmed'] = all_data_df['Confirmed'].apply(lambda x: fix_decimal(x))

    # fix decimal point for multiple data
    country_data_df.loc[country_data_df['quarantine']==' ', 'quarantine'] = 0
    for feature in ['ati', 'quarantine', 'isolation', 'tests']:
        country_data_df[feature] = country_data_df[feature].apply(lambda x: fix_decimal(x))
        
    return all_data_df, country_data_df

        
def save_data(all_data_df, country_data_df):
    for date in all_data_df.Date.unique():
        d_df = all_data_df.loc[all_data_df.Date==date]
        d_df.to_csv(os.path.join('ro_covid_19_daily_reports', f"{date}.csv"), index=False)    

    all_data_df.to_csv(os.path.join('ro_covid_19_time_series', "ro_covid_19_time_series.csv"), index=False)
    country_data_df.to_csv(os.path.join('ro_covid_19_time_series', "ro_covid_19_country_data_time_series.csv"), index=False)

def check_data(all_data_df):    
    print(f"All data cases: {all_data_df.groupby('Date')['Confirmed'].sum()}")

import datetime as dt
          
def main():        
    all_data_df, country_data_df = parse_content()
    check_number_of_counties(all_data_df)
    all_data_df, country_data_df = data_cleaning(all_data_df, country_data_df)
    check_data(all_data_df)
    save_data(all_data_df, country_data_df)
    
if __name__ == "__main__":
    main()

    
    