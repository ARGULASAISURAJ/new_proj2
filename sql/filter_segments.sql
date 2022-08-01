SELECT
CASE
WHEN v5_flag = 1 THEN root_folder
ELSE ps_id
END as ps_id, 
ps_name,
CAST(ps_population AS INTEGER) AS ps_population,
v5_flag, 
folder_name,
segment_id, 
segment_name,
CAST(segment_population AS INTEGER) AS segment_population,
rule
FROM ${project_prefix}_ps_stats
WHERE v5_flag in (${filters.v5_flag})
AND REGEXP_LIKE(lower(ps_name), '${filters.ps_to_include}')
AND REGEXP_LIKE(lower(folder_name), '${filters.folders_to_include}')
AND REGEXP_LIKE(lower(segment_name), '${filters.segments_to_include}')
AND segment_name IS NOT NULL
AND segment_population > 0
AND length(rule) > 8