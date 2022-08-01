WITH T2 AS (
SELECT T1.*,
lead(segment_query, 1) over (partition by segment_name order by event_date desc ) as last_query
FROM ${project_prefix}_final_metrics_table T1
)
SELECT T2.event_date, 
T2.segment_name, 
T2.segment_query, 
T2.last_query,
CASE 
WHEN segment_query = last_query OR last_query IS NULL THEN 0
ELSE 1
END as query_change
FROM T2