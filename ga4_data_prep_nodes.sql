WITH pageviews AS (
  SELECT
    (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "page_location") AS page_location,
    COUNT(*) AS pageview_count
  FROM avisia-analytics.analytics_271196011.events_20250201
  WHERE event_name = "page_view"
  GROUP BY page_location
)
SELECT page_location, pageview_count
FROM pageviews
ORDER BY pageview_count DESC;
