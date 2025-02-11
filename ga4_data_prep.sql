WITH pageviews AS (
  SELECT
    user_pseudo_id,
    event_bundle_sequence_id,
    event_timestamp,
    event_name,
    (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "page_location") AS page_location,
    (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "session_source") AS session_source,
    (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "session_medium") AS session_medium,
    (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "session_campaign") AS session_campaign,
    COALESCE(
      (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "session_default_channel_group"), 
      "Direct"
    ) AS default_channel_group  -- Ensure "Direct" is assigned when NULL
  FROM `avisia-analytics.analytics_271196011.events_20250201`
  WHERE event_name = "page_view"
),
transitions AS (
  SELECT
    p1.user_pseudo_id,
    p1.page_location AS from_page,
    p2.page_location AS to_page,
    p1.event_timestamp AS from_time,
    p2.event_timestamp AS to_time
  FROM pageviews p1
  JOIN pageviews p2
  ON p1.user_pseudo_id = p2.user_pseudo_id
  AND p2.event_timestamp > p1.event_timestamp
  ORDER BY p1.user_pseudo_id, p1.event_timestamp
),
entry_points AS (
  -- Find the first page of each session and associate it with a traffic source
  SELECT
    user_pseudo_id,
    MIN(event_timestamp) AS first_time,
    ANY_VALUE(page_location) AS entry_page,
    ANY_VALUE(default_channel_group) AS entry_channel
  FROM pageviews
  GROUP BY user_pseudo_id
),
exit_points AS (
  -- Find the last page of each user session
  SELECT
    user_pseudo_id,
    MAX(event_timestamp) AS last_time,
    ANY_VALUE(page_location) AS exit_page
  FROM pageviews
  GROUP BY user_pseudo_id
)
-- Final result: main transitions + entry & exit pages
SELECT 
  t.from_page, 
  t.to_page, 
  COUNT(*) AS transition_count,
  NULL AS entry_channel  -- Placeholder for merging entry nodes later
FROM transitions t
GROUP BY from_page, to_page

UNION ALL

-- Entry nodes: Create artificial links from the entry channel to the entry page
SELECT 
  e.entry_channel AS from_page, 
  e.entry_page AS to_page, 
  COUNT(*) AS transition_count,
  e.entry_channel
FROM entry_points e
GROUP BY entry_channel, entry_page

UNION ALL

-- Exit nodes: Create artificial links from exit pages to "EXIT" node
SELECT 
  e.exit_page AS from_page, 
  "EXIT" AS to_page, 
  COUNT(*) AS transition_count,
  NULL AS entry_channel
FROM exit_points e
GROUP BY exit_page;
