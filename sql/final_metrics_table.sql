WITH LAST AS (
SELECT  DISTINCT time, segment_id, segment_query, segment_population 
FROM ${project_prefix}_final_metrics_table
WHERE time = (SELECT MAX(time) FROM ${project_prefix}_final_metrics_table)
)
SELECT 
TD_TIME_STRING(NEW.time, 'd!') as event_date,
NEW.*,
CASE
WHEN LAST.segment_population IS NULL THEN 1
ELSE 0
END as query_change,
CAST(NEW.time as DOUBLE) as date_unixtime
FROM ${project_prefix}_metrics_join NEW
LEFT JOIN LAST
on LAST.segment_query = NEW.segment_query AND LAST.segment_id = NEW.segment_id