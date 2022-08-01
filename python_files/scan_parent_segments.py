import tdclient
import requests
import json
import pytd
import pytd.pandas_td as td
import pandas as pd
import os
import sys
import numpy as np

apikey = os.environ['TD_API_KEY'] 
tdserver = os.environ['TD_API_SERVER']
sink_database = os.environ['SINK_DB']
folder_depth = os.environ['FOLDER_DEPTH']
output_table = os.environ['OUTPUT_TABLE']
segment_api = tdserver.replace('api', 'api-cdp')
headers= {"Authorization":'TD1 '+ apikey, "content-type": "application/json"}

############ Function to Read JSON #####################
def json_extract(url):
    #Get Segment Info JSON from Master Segment using TD API
    get_info = requests.get(url, headers=headers)

    return get_info.json()

##########Function to extract Parent Segment Info from V4 and V5 ###########
def get_ps_list():
    v4_segment_list = f'https://{segment_api}/audiences'
    v5_segments_list = f'https://{segment_api}/entities/parent_segments'
    
    v4_ps = json_extract(v4_segment_list)
    v5_ps = json_extract(v5_segments_list)
    
    v4_dic = dict(ps_id = [], ps_name = [], ps_population = [], root_folder = [])
    
    for item in v4_ps:
        v4_dic['ps_id'].append(item['id'])
        v4_dic['ps_name'].append(item['name'])
        v4_dic['ps_population'].append(item['population'])
        v4_dic['root_folder'].append(item['rootFolderId'])
        
    v4_df = pd.DataFrame(v4_dic)
    v4_df.fillna(0, inplace = True)
    v4_df['v5_flag'] = 0
    
    try:
        v5_ps_data = v5_ps['data']
        v5_ids = [item['id'] for item in v5_ps_data]
        v5_df = v4_df[v4_df.ps_id.isin(v5_ids)].copy()
        v5_df['v5_flag'] = 1

        roots = list(v5_df.ps_id)
        psids = list(v5_df.root_folder)

        v5_df['ps_id'], v5_df['root_folder'] = psids, roots
        v5_df['ps_name'] = [item + " Root" for item in list(v5_df.ps_name)]
        
        new_df = pd.concat([v4_df, v5_df])
        new_df.reset_index(drop = True, inplace = True)
        
        return new_df
    
    except:
        print("No Parent Segments built in V5")
                     
        return v4_df

######## Function to extract Folder Info from V4 and V5 ################
def get_folder_list(ps_df):
    v4_ps = list(ps_df[ps_df.v5_flag == 0].ps_id)
    v5_ps = list(ps_df[ps_df.v5_flag == 1].ps_id)
    
    combined_folders = []

    for master_id in v4_ps:
        try:
            v4_url_folders = f'https://{segment_api}/audiences/{master_id}/folders'
            v4_json = json_extract(v4_url_folders)

            folders = [{'ps_id': master_id, 'folder_id': item['id'], 'folder_name': item['name']} for item in v4_json]
            combined_folders.extend(folders)
        except:
            print(f"No Audience Segments built V4 for Parent Segment - {master_id}")

    if len(v5_ps) > 0:
        for master_id in v5_ps:
            v5_url_folders = f'https://{segment_api}/entities/by-folder/{master_id}?depth={folder_depth}'
            v5_json = json_extract(v5_url_folders)['data']

            folders = [{'ps_id': master_id, 'folder_id': item['id'], 'folder_name': item['attributes']['name']} for item in v5_json]
            combined_folders.extend(folders)
            
    return pd.DataFrame(combined_folders)

################## Function to extract Segment Info from V4 and V5 #############
def get_segment_list(ps_df):
    v4_ps = list(ps_df[ps_df.v5_flag == 0].ps_id)
    v5_ps = list(ps_df[ps_df.v5_flag == 1].ps_id)
    
    combined_segments = []

    for master_id in v4_ps:
        v4_url_segments = f'https://{segment_api}/audiences/{master_id}/segments'
        v4_json = json_extract(v4_url_segments)

        segments = [{'folder_id': item['segmentFolderId'], 'segment_id': item['id'], 'segment_name': item['name'],
                    'segment_population': item['population'], 'realtime': item['realtime'], 'rule': item['rule']} for item in v4_json]
        
        combined_segments.extend(segments)

    if len(v5_ps) > 0:
        for master_id in v5_ps:
            v5_url_segments = f'https://{segment_api}/entities/by-folder/{master_id}?depth=10'
            v5_json = json_extract(v5_url_segments)['data']
            segment_json = [item for item in v5_json if item['type'].startswith('segment-')]

            segments = [{'folder_id': item['relationships']['parentFolder']['data']['id'], 'segment_id': item['id'], 
                         'segment_name': item['attributes']['name'],'segment_population': item['attributes']['population'], 
                         'realtime': item['type'], 'rule': item['attributes']['rule']} for item in segment_json]
            
            combined_segments.extend(segments)
            
    segment_df = pd.DataFrame(combined_segments)
    segment_df.realtime = [1 if item == True or str(item).startswith('segment-re') else 0 for item in list(segment_df.realtime)]
            
    return segment_df

def extract_segment_stats():

    #get Parent Segment DF
    ps_df = get_ps_list()

    #get Folder Info DF
    folders_df = get_folder_list(ps_df)

    #Merge both DFs on ps_id
    combined_df = pd.merge(ps_df, folders_df, on="ps_id", how = 'left')

    #Get Folder Segments Info
    segments_df = get_segment_list(ps_df)

    #Merge Segments DF into combined on folder_id
    final_df = pd.merge(combined_df, segments_df, on="folder_id", how = 'left')

    #Replace NaN with 0 for numeric columns and drop duplicate columns caused by v4/v5 segment name overlap
    final_df.segment_population.fillna(0, inplace = True)
    final_df.realtime.fillna(0, inplace = True)
    final_df.dropna(subset = ['segment_id'], inplace = True)
    final_df.drop_duplicates(subset=['root_folder', 'folder_id', 'folder_name', 'segment_id', 'segment_name'], keep='first', inplace=True, ignore_index=False)

    final_df.info()
    final_df.head()

    #Write final_df to TD
    client = pytd.Client(apikey=apikey, endpoint=tdserver, database=sink_database)
    client.load_table_from_dataframe(final_df, output_table, writer='bulk_import', if_exists='overwrite')