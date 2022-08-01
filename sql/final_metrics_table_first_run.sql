SELECT 
TD_TIME_STRING(time, 'd!') as event_date,
T1.*,
0 as query_change,
CAST(time as DOUBLE) as date_unixtime
FROM ${project_prefix}_metrics_join T1