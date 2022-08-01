import tdclient
import requests
import json
import pytd
import pytd.pandas_td as td
import pandas as pd
import os
import sys

#Write Queries to Temp Table
def extract_queries():

    apikey = os.environ['TD_API_KEY'] 
    tdserver = os.environ['TD_API_SERVER']
    segment_api = tdserver.replace('api', 'api-cdp')
    sink_database = os.environ['SINK_DB']
    unique_id = os.environ['UNIQUE_ID']
    unique_id2 = os.environ['UNIQUE_ID2']
    output_table = os.environ['OUTPUT_TABLE']

    print(output_table)

    headers= {"Authorization":'TD1 '+ apikey, "content-type": "application/json"}

    #Load profile_mapping_temp_table
    query_syntax = f'SELECT * FROM {output_table}'
    
    client = pytd.Client(apikey=apikey, endpoint=tdserver, database=sink_database)
    results = client.query(query_syntax, engine='presto')
    new_tab =  pd.DataFrame(**results)
    
    #Exctract queries for each segment
    queries = []
    for item in list(zip(new_tab.ps_id, new_tab.rule, new_tab.ps_name, new_tab.ps_population, new_tab.v5_flag, new_tab.folder_name, new_tab.segment_name, new_tab.segment_population, new_tab.segment_id)):
        rule = {"rule": eval(item[1]), "format":"sql"}
        mastersegment_id = item[0]
        ps_name = item[2]
        ps_population = item[3]
        v5_flag = item[4]
        folder_name = item[5]
        segment_name = item[6]
        segment_population = item[7]
        segment_id = item[8]

        #Write query
        post = requests.post(f'https://{segment_api}/audiences/{mastersegment_id}/segments/query', headers=headers, json=rule)
        segment_query = post.json()['sql']

        #Add unique user_id to query
        segment_query = segment_query.split()
        segment_query[1] = f"a.{unique_id},a.{unique_id2}, '{ps_name}' as ps_name, {ps_population} as ps_population, {v5_flag} as v5_flag, '{folder_name}' AS folder_name, {segment_id} AS segment_id, '{segment_name}' as segment_name, {segment_population} AS segment_population"
        segment_query = " ".join(segment_query)

        queries.append(segment_query)
     
    #Create final table
    new_tab['segment_query'] = queries
    
    client.load_table_from_dataframe(new_tab, output_table, writer='bulk_import', if_exists='overwrite')

    