SELECT
T1.*,
T2.${table.metric}_uniques,
T2.${table.metric}_total,
T2.${table.metric}_average
from ${project_prefix}_metrics_join T1
left join ${project_prefix}_${table.metric} T2 
on T1.segment_id = T2.segment_id
-- on T1.ps_name=T2.ps_name AND T1.segment_name=T2.segment_name