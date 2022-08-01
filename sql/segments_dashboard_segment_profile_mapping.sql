SELECT 
-- td_canonical_id,
ps_name,
CAST(ps_population AS INTEGER) as ps_population,
v5_flag,
folder_name,
segment_id,
segment_name,
CAST(segment_population AS INTEGER) as segment_population,
REPLACE(SPLIT(segment_query, 'customers" a ')[2], 'where', 'WHERE') as segment_query
FROM ${project_prefix}_segment_profile_mapping_temp
