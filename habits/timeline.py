"""
Swimlane timeline layout — the interval-partitioning + column-packing
algorithm behind the day view. Deliberately pure Python (no Django
imports) so it's testable in isolation from the ORM/request cycle.

Approach (a simplified version of the classic calendar-event layout
algorithm):
  1. Sort events by start time.
  2. Walk through in order, grouping into "clusters" — a new cluster
     starts whenever an event begins at or after every event seen so
     far in the current cluster has ended. Events in different
     clusters never visually overlap, so each cluster gets its own
     independent lane count (an event with no overlapping neighbors
     gets full width, rather than being squeezed to match some
     unrelated event elsewhere in the day).
  3. Within a cluster, greedily assign each event to the first lane
     whose last-placed event already ended by this event's start —
     same idea as the "minimum number of meeting rooms" problem.

NOT implemented: the fancier "expand into unused width" refinement
some calendar apps do (e.g. an event alone in the right half of a
cluster stretching to fill it). Every event in a cluster gets equal
width instead — simpler, and a reasonable-looking result in practice.
"""

DEFAULT_DURATION_MINUTES = 30  # visual fallback when a habit has no duration set


def compute_timeline_layout(events, window_start, window_end):
    """
    events: list of dicts, each with at least 'start' and 'duration'
            (both in minutes-from-midnight / minutes). Any other keys
            are carried through untouched.
    window_start, window_end: minutes-from-midnight bounding the
            rendered day (e.g. 6*60 to 22*60 for a 6am-10pm view).

    Returns a new list (same dicts, mutated with layout keys) sorted
    by start time:
      - clipped_start, clipped_end: event times clamped into the window
      - top_pct, height_pct: vertical position/size as % of window
      - left_pct, width_pct: horizontal position/size as % of its cluster
      - lane, cluster_lanes: raw column info, in case a template wants it
    Events entirely outside the window are clipped to a 1-minute sliver
    at the nearest edge rather than dropped, so nothing silently
    disappears from the view.
    """
    window_total = window_end - window_start
    if window_total <= 0:
        return []

    working = []
    for item in events:
        start = item['start']
        end = start + item['duration']
        clipped_start = max(start, window_start)
        clipped_end = min(end, window_end)
        if clipped_end <= clipped_start:
            # Entirely outside the window (or zero-duration) — show a
            # minimal sliver at the nearest edge instead of dropping it.
            clipped_start = min(max(clipped_start, window_start), window_end - 1)
            clipped_end = clipped_start + 1
        working.append({**item, 'clipped_start': clipped_start, 'clipped_end': clipped_end})

    working.sort(key=lambda e: (e['clipped_start'], -e['clipped_end']))

    clusters = []
    current_cluster = []
    cluster_max_end = None
    for e in working:
        if current_cluster and e['clipped_start'] >= cluster_max_end:
            clusters.append(current_cluster)
            current_cluster = []
            cluster_max_end = None
        current_cluster.append(e)
        cluster_max_end = e['clipped_end'] if cluster_max_end is None else max(cluster_max_end, e['clipped_end'])
    if current_cluster:
        clusters.append(current_cluster)

    result = []
    for cluster in clusters:
        columns_last_end = []
        for e in cluster:  # already in start-time order from the global sort
            placed = False
            for col_idx, last_end in enumerate(columns_last_end):
                if e['clipped_start'] >= last_end:
                    columns_last_end[col_idx] = e['clipped_end']
                    e['lane'] = col_idx
                    placed = True
                    break
            if not placed:
                columns_last_end.append(e['clipped_end'])
                e['lane'] = len(columns_last_end) - 1
        total_lanes = len(columns_last_end)
        for e in cluster:
            e['cluster_lanes'] = total_lanes
            result.append(e)

    for e in result:
        e['top_pct'] = round((e['clipped_start'] - window_start) / window_total * 100, 3)
        e['height_pct'] = round((e['clipped_end'] - e['clipped_start']) / window_total * 100, 3)
        e['left_pct'] = round(e['lane'] / e['cluster_lanes'] * 100, 3)
        e['width_pct'] = round(100 / e['cluster_lanes'], 3)

    return result