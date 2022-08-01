WITH BASE AS (
  SELECT * FROM ${table.src_db}.${table.src_table}
  WHERE TD_TIME_RANGE(${table.unixtime_col}, '${filters.time_range_start_date}', '${filters.time_range_end_date}')
),
T2 AS (
SELECT ${table.join_key},
${table.agg}(TRY(CAST(${table.agg_col_name} AS DOUBLE))) as ${table.metric} 
FROM BASE
${table.filter}
group by ${table.join_key}
),
T3 AS (
SELECT T1.${table.join_key},
T1.ps_name,
T1.segment_id,
T1.segment_name,
T1.time,
T2.${table.metric}
FROM ${project_prefix}_run_query T1
JOIN T2 on T1.${table.join_key} = T2.${table.join_key}
)
SELECT 
ps_name,
segment_id,
segment_name,
APPROX_DISTINCT(${table.join_key}) as ${table.metric}_uniques,
ROUND(SUM(${table.metric}), 2) as ${table.metric}_total,
ROUND(AVG(${table.metric}), 2) as ${table.metric}_average 
FROM T3 
GROUP BY ps_name, segment_id, segment_name