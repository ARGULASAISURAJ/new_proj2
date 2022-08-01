

> Written with [StackEdit](https://stackedit.io/)
# Package Overview 

The purpose of this solution is to allow CDP users (marketers, campaign analysts, etc.) to track important KPIs for the Audiences they build  and activate for marketing campaigns in Treasure Data Audience Studio. The Dashboard allows to filter and compare specific segments by Segment Name and Time Period. Some of the OTB metrics include: 

- High Leveldada Summary of Counts and Population sizes for Parent Segment, Audience Studio Folders, and Audience Studio Segments in the given TD account

- Filter Segments by Parent Segment Name, Folder Name and track KPIs such as:

- Segment Population growth over time (Daily, Weekly, etc.)

- Total & AVG Order Value

- Total, Unique & AVG number of items purchased

- Total, Unique & AVG number of pageviews

- Total, Unique & AVG number of email events (clicks/opens/sends etc.)

- Track Business Rules Changes for each segment 

- More Custom Metrics can be added after installation upon Customer Request


## Use Cases

 - Track Campaign KPIs across Audiences build in Treasure Data
 - Gain valuable business insights and optimize marketing campaigns
 - Easily track daily performance of A/B Testing Segments
 - Catch unauthorized Segment Rule changes that might affect population size and performance negatively and revert back to previous logic
 - Measure and communicate the business value of CDP across your org


# Prerequisites and Limitations



* TD Account must have ***Treasure Insights enabled*** 
* TD User isntalling the package must have ***Edit Data Models & Dashboards*** TI permissions in TD
* TD User isntalling the package must have ***Workflow Edit & Run*** permissions in TD and must have access to the databases where the tables with the KPI metrics live.
* It is recommended that you monitor ***datamodel size*** monthly in the V5 console under the `Insights Models` tab and ensure it does not exceed ***4GB*** over time. This should not happen with the OTB configuration, so please contact your TD rep in the rare event that this occurs. 


# Configuring Workflow Parameters

The workflow is set-up, so that the end user only needs to configure the `.yml` files in the `config\` folder and the `config.json` file in main project folder and the Workflow can be ran to execute end-to-end code automatically. In fact, these files are ***autoamtically configured for you*** during the Package installation steps above, as the parameters you are entering in the UI will be dynamically popualted in the proper lines inside the `yml & json` config files.
However, you can modify these params after installation manually when further customization of the solution is needed to fit additional data context and use cases that might not be covered by the OTB configuration. Please note that this is ***ONLY recommended for technical users*** with some experience with `DigDag and SQL/Python`. If customer does not have such resources available, please reach out to your TD rep and we can help customize some of the code to your needs when possible. Details on how to configure each yml or config file below:



1. `config/input_params.yml` - Controls important parameters which are often applied globally across most of the data sources and processes in the workflow.

```
########################## GLOBAL PARAMS ############################

project_prefix: segment_analytics #all output tables and project sub-workflows will start with this prefix
sink_database: ml_dev

######################## FILTER PARAMS ##############################

filters:
  v5_flag: 1, 0                         #'1' - will only scan segments in V5, 0 - only in V4
  ps_to_include: 'ml_|test'             #use lower letter REGEXP notation to only scan selected Parent Segments that include 'ml_' in their name (leave blank to scan all)
  folders_to_include: 'rfm|nba|next'    #use lower letter REGEXP notation to only scan selected Audience Studio Folders that include 'rfm OR nba OR next' in their name  (leave blank to scan all)
  segments_to_include:                  #use lower letter REGEXP notation such as 'segment_name|segment_name_2|segment_name_3' to only scan selected Segments (leave blank to scan all)
  apply_time_filter: 'yes'              #yes - applies time filter to aggregate metrics tables
  time_filter_type: TD_INTERVAL         #Use TD_TIME_RANGE to specify fixed start/end dates OR 'TD_INTERVAL' to lookback days/weeks/months from now
  time_range_start_date: 2020-11-01     #Defines start date for`TD_TIME_RANGE` use format YYYY-MM-DD
  time_range_end_date: 2222-02-02       #To always end TIME_RANGE at the latest available date, leave default as '222-02-02'. To end on a custom date use format YYYY-MM-DD
  time_interval_start_date: now         #leave default 'now' to start at today's date and lookback using 'lookback period', or change to a custom start_date in YYYY-MM-DD format
  lookback_period: -20M                 #-1M looksback a month, -30d looks back 30 days, - 2w looksback 2 weeks etc. Used only with TD_INTERVAL

############# TABLE PARAMS FOR SOURCE AND OUTPUT TABLES #############

aggregate_metrics_tables: #list of input behavior tables you want to aggregate KPI metrics for
 - metric: email_sends
    agg: count
    agg_col_name: '1' #We use '1' instead of '*' because in some instances we might want to SUM(agg_col_name)
    src_db: ml_dev
    src_table: tb_email_activity_combined
    join_key: td_canonical_id
    unixtime_col: time
    filter: WHERE event_type = 'send'
    
  - metric: spend
    agg: sum
    agg_col_name: order_value
    src_db: ml_dev
    src_table: tb_transactions_mock
    join_key: td_canonical_id
    unixtime_col: time
    filter:             #Add custom 'WHERE' CLAUSE filter if needed

  - metric: orders_count
    agg: count
    agg_col_name: '1'
    src_db: ml_dev
    src_table: tb_transactions_mock
    join_key: td_canonical_id
    unixtime_col: time
    filter:
```

2. `config.json` - Controls important parameters used by Python Custom Scripting `.py` files to create the final JSON for the Datamodel and build & share it via API.

```"model_name":  "Segments_dashboard_v5" (name of datamodel)
,
"model_tables": [
                ] (list of tables to be added to datamodel)
,
"shared_user_list": [ "dilyan.kovachev+psdemo@treasure-data.com"] (list of users to share datamodel with)
,
"change_schema_cols": {"date": ["run_date", "event_time"], "text": ["ENTER_NAME"], "float": ["ENTER_NAME"], "bigint": ["ENTER_NAME"]} (list of columns you want to change datatype from raw table to datamodel. Ex. in "date" you provide column names that will be converted to `datetime`)
,
"join_relations": {"pairs":[]
                  }
} (if any joins were required you can add a list of table_name:join_key pairs)
```


# Explanation of Workflow Tasks, Code and Table Outputs

## DigDag Tasks Summary

- ***segment_analytics_launch.dig*** - runs the main project workflow, that triggers entire project execution end to end, including all sub-workflows and queries in project folder.

- ***segment_analytics_scan_parent_segments.dig***  - scans the Segment API and extracts all the Parent Segment Names, Folder Names, Audience Segment Names and their corresponding IDs, Populations and Query Rules and stores them in a table in TD. This allows us to dynamically scan this table later when we want to aggregate metrics for a selected set of Segments/Audiences.

- ***Segments_dashboard_data_prep.dig***  - reads from the `input_params.yml` and executes a list of sub-workflows that will dynamically extract the canonical_ids of the desired segment populations from Audience Studio, by running the query_rules stored in the the Segment API JSON for each Segment, and then aggregating the KPIs defined in the `${aggregate_metrics_tables}` list in the `input_params.yml`. These processes are controlled by the sub-workflows:

 - ***segments_dashboard_map_segments_to_profiles.dig***  - retrieves all the segment names, ids and the query logic that we have selected using our `${filter}` params in the `input_params.yml` and the  ***segment_analytics_ps_stats*** table. After that it runs each query to get the list of `canonical_ids` for each Segment and loops through all the tables in the `${aggregate_metrics_tables}` list and aggregates the desired metrics by Segment Name, grouping by the extracted canonical_ids.

- ***Segments_dashboard_join_tables.dig***  - loops through the final list of aggregates metrics and joins them all in one final output table.

- ***Segments_dashboard_datamodel_create.dig***  - creates the datamodel that powers the Dashboard by reading from the `config.json file`.

- ***Segments_dashboard_datamodel_build.dig***  - updates the existing datamodel/dashboard with the latest data generated by each workflow run.


## SQL Queries

- ***sql/filter_segments.sql*** - this reads the params `${filters}` from the `input_params.yml` config file and selects only the `ids` and `names` of the Parent Segments, Folders, and Audiences that the end user wants to make available in the final dashboard for analysis. See snippet below: 

```
AND REGEXP_LIKE(lower(ps_name), '${filters.ps_to_include}')
AND REGEXP_LIKE(lower(folder_name), '${filters.folders_to_include}')
AND REGEXP_LIKE(lower(segment_name), '${filters.segments_to_include}')
```
- ***sql/segments_dashboard_get_query.sql*** - this reads from the `segment_analytics_segment_profile_mapping_temp` table and extracts the SQL Query Syntax behind building each audience in the Audience Studio in order to get the `canonical_ids` that belong to each Audience and inserts the ids into the `segment_analytics_run_query` table along with the corresponding Audience Name, ID flag, and population counts.

- ***sql/segments_dashboard_metrics_agg.sql*** - This loops through the `${aggregate_metrics_tables}` list defined in the `input_params.yml` config file and calculates the ***total, avg, and unique*** aggregate metric for each Audience ID saved earlier in the `segment_analytics_run_query table`. Each aggregate metric is then saved as an individual temp table with the `segment_analytics_` + `metric_name` naming convention (Ex. ***segment_analytics_pageviews_total***). 

- ***sql/final_metrics_table.sql*** - this query then joins each of the agg_metric_temp_tables into one final table - `segment_analytics_final_metrics_table`. This is the table that contains all the important KPIs associated with each Audience Segment that the user defined earlier in the `${filters.folders_to_include}, ${filters.segments_to_include}` params. This table powers the final Segment Analytics Dashboard widgets and filters.

## Table Outputs

- ***segment_analytics_ps_stats*** - summary of stats across all Parent Segments, Audience Folders, and Audience Segments that exist in V5 or V4 in TD account. This table is used to filter out which Audience Segments you want to include in the Dashboard as well as to present the High-Level Summary statistics in the `TD Account Summary Tab` in the Dashboard.

| ps_id | ps_name |v5_flag|folder_id|folder_name|segment_id|segment_name|segment population|
|-------|---------|-------|---------|-----------|----------|------------|------------------|
| 24145 | Demos   |   1   |51444    |RFM Models |12451     |Top Tier    |1,245,000         |

- ***segments_dashboard_final_metrics_table*** - Final Table with all segment metrics that will be shown in the Dashboard pre-aggregated by Segment_Name and Date.

| event_date | segment name |population|pageviews_total|order_value|email_opens|order_counts|
|------------|--------------|----------|---------------|-----------|-----------|------------|
| 2022-05-20 | RFM Models   |124500    | 725000        | 34525     | 12451     |  42777     |

### Datamodel & Dashboard Overview

The `Segment Analytics Dashboard` reads from an Insights Model build from the params listed in the `config.json` file. By Default this includes the two  tables listed above- ***segment_analytics_ps_stats and segments_dashboard_final_metrics_table***.   More tables and metrics can be added upon customer request to fulfill additional Use Case Requirements.


### Dashboard Screenshots

1. **TD Account Parent Segment & Audience Studio Summary** - 
High Level Summary of Counts and Population sizes for `Parent Segment, Audience Studio Folders, and Audience Studio Segments` in the given TD account.

(To add an image, add an exclamation mark (`!`), followed by alt text in brackets, and the path or URL to the image asset in parentheses. You can optionally add a title in quotation marks after the path or URL.)
![ Title of Image](path or url to image)

2. **Audience Population Metrics** - 
Provides Widgets for KPIs such as `Query Logic Changes Tracker, Latest Population by Segment Name, Daily/Weekly Population Growth Tracker etc.`


3. **Web Activity Metrics** - 
Provides Widgets for tracking `Total, Unique & AVG` Daily/Weekly web-events for each Segment Audience. It also shows the ***Latest*** Totals and AVGs of each metric compared by Segment Name. This allows to find Segments that `generate a lot more web-engagement` for the customer, track `how web-activity grows over time` and `measure the effect of different marketing initiatives` on web engagement.


4. **Orders/Sales Metrics** - 
Provides Widgets for tracking `Total, Unique & AVG` Daily/Weekly Revenue for each Segment Audience. It also shows the ***Latest*** Totals and AVGs of each metric compared by Segment Name. This allows to find Segments that `generate a lot more sales and revenue` for the customer, track `how Sales/Revenue grows over time` and measure the effect of different `marketing initiatives on revenue growth`.

5. **Email Activity Metrics** - 
Provides Widgets for tracking `Total, Unique & AVG` Daily/Weekly email-activity (`sends, opens, clicks`) for each Segment Audience. It also shows the ***Latest*** Totals and AVGs of each metric compared by Segment Name. This allows to find Segments that `generate a lot more email engagement` for the customer, track `how email activity grows over time`.

5. **Others** - 
This last widget is reserved for additional custom metrics that can be added in a table format, that might be of use to the customer depending on their input data and use cases. OTB we’ve included ability to ***detect Audience Query Logic Change and visualize the actual Query Change Syntax*** as well as compare Segments metrics by **Totals vs Uniques**. Data Engineers / Analysts who are comfortable with WOrkflows and Treasure Insights can easily add more custom metrics to this dashboard by using the Workflow `config` files and custom SQL queries.


### Additional Code Examples

#### 1. Important SQL Queries

- ***sql/filter_segments.sql*** - this reads the params `${filters}` from the `input_params.yml` config file and selects only the `ids` and `names` of the Parent Segments, Folders, and Audiences that the end user wants to make available in the final dashboard for analysis. See snippet below: 

```
AND REGEXP_LIKE(lower(ps_name), '${filters.ps_to_include}')
AND REGEXP_LIKE(lower(folder_name), '${filters.folders_to_include}')
AND REGEXP_LIKE(lower(segment_name), '${filters.segments_to_include}')
```
- ***sql/segments_dashboard_get_query.sql*** - this reads from the `segment_analytics_segment_profile_mapping_temp` table and extracts the SQL Query Syntax behind building each audience in the Audience Studio in order to get the `canonical_ids` that belong to each Audience and inserts the ids into the `segment_analytics_run_query` table along with the corresponding Audience Name, ID flag, and population counts.

- ***sql/segments_dashboard_metrics_agg.sql*** - This loops through the `${aggregate_metrics_tables}` list defined in the `input_params.yml` config file and calculates the ***total, avg, and unique*** aggregate metric for each Audience ID saved earlier in the `segment_analytics_run_query table`. Each aggregate metric is then saved as an individual temp table with the `segment_analytics_` + `metric_name` naming convention (Ex. ***segment_analytics_pageviews_total***). 

- ***sql/final_metrics_table.sql*** - this query then joins each of the agg_metric_temp_tables into one final table - `segment_analytics_final_metrics_table`. This is the table that contains all the important KPIs associated with each Audience Segment that the user defined earlier in the `${filters.folders_to_include}, ${filters.segments_to_include}` params. This table powers the final Segment Analytics Dashboard widgets and filters.

# Additional Information

### 1. How to schedule workflow?
Find the installed workflow project and locate the `segment_analytics_launch.dig` file, which is the main project file that runs the entire end-to-end solution. Click `Launch Project Editor` on the top right in the console and then click `Edit File` on bottom right. At the very top of the file you might see an empty section as such:
```
###################### SCHEDULE PARAMS ##################################  
```
In order to schedule the workflow, please add syntax below, so the final syntax looks as such:
```
###################### SCHEDULE PARAMS ##################################  
timezone: UTC

schedule:
  daily>: 07:00:00
```
The above example will automatically run the workflow ***every day at 7:00am*** UTC time. For more scheduling options, please refer to the DigDag documentation at [Link](https://docs.digdag.io/scheduling_workflow.html#setting-up-a-schedule)

### 2. What should I do if I need Tech Support on setting up the solution in my TD account?

Please contact your TD representative and they will be able to dedicate an Engineering resource that can help guide you through the installation process and help you with any troubleshooting or code customizations if needed. 


