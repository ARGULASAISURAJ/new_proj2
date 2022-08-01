SELECT

'${project_prefix}_metrics_join' as table_name

UNION ALL

SELECT '${project_prefix}_run_query' as table_name

UNION ALL

SELECT '${project_prefix}_segment_profile_mapping' as table_name

UNION ALL

SELECT '${project_prefix}_segment_profile_mapping_temp' as table_name