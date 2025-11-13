WITH pageviews AS (
  SELECT
    user_pseudo_id,
    SAFE_CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key = "ga_session_id") AS STRING) AS session_id,
    event_timestamp,
    (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "page_location") AS page_location,
    COALESCE(
      (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "session_default_channel_group"), 
      "Direct"
    ) AS default_channel_group
  FROM `avisia-analytics.analytics_271196011.events_20250201`
  WHERE event_name = "page_view"
),
ordered_pageviews AS (
  -- Assign an order to pageviews per session
  SELECT 
    *,
    ROW_NUMBER() OVER (PARTITION BY user_pseudo_id, session_id ORDER BY event_timestamp) AS pageview_order
  FROM pageviews
),
transitions AS (
  -- Join each pageview to the next pageview in the same session
  SELECT
    p1.page_location AS from_page,
    COALESCE(p2.page_location, "EXIT") AS to_page  -- Assign "EXIT" only once here
  FROM ordered_pageviews p1
  LEFT JOIN ordered_pageviews p2
    ON p1.user_pseudo_id = p2.user_pseudo_id
    AND p1.session_id = p2.session_id
    AND p2.pageview_order = p1.pageview_order + 1
),
entry_points AS (
  -- Get the first page per session with its source
  SELECT
    user_pseudo_id,
    session_id,
    MIN(event_timestamp) AS first_time,
    ANY_VALUE(page_location) AS entry_page,
    ANY_VALUE(default_channel_group) AS entry_channel
  FROM pageviews
  GROUP BY user_pseudo_id, session_id
)
-- Final result: main transitions + entry pages
SELECT 
  t.from_page, 
  t.to_page, 
  COUNT(*) AS transition_count,
  NULL AS entry_channel
FROM transitions t
GROUP BY from_page, to_page

UNION ALL

-- Entry nodes: Create artificial links from entry channel to the entry page
SELECT 
  e.entry_channel AS from_page, 
  e.entry_page AS to_page, 
  COUNT(*) AS transition_count,
  e.entry_channel
FROM entry_points e
GROUP BY entry_channel, entry_page;
