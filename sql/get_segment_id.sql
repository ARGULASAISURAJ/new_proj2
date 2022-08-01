SELECT 
ps_id, 
segment_id, 
rule
FROM  ${project_prefix}_segment_profile_mapping_temp
WHERE folder_name = 'RFM Segments'