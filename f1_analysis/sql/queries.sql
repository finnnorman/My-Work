-- ============================================================
-- F1 Strategy Analysis Queries
-- ============================================================


-- ------------------------------------------------------------
-- Q1: Average lap time per compound per driver in a given race
-- ------------------------------------------------------------
-- Shows how each tire compound performed (pace-wise) per driver
-- Usage: pass ?1 = race_id
-- ------------------------------------------------------------
SELECT
    r.grand_prix,
    d.full_name          AS driver,
    d.team,
    ts.compound,
    COUNT(lt.lap_id)     AS laps_sampled,
    ROUND(AVG(lt.lap_time_ms) / 1000.0, 3) AS avg_lap_sec,
    ROUND(MIN(lt.lap_time_ms) / 1000.0, 3) AS best_lap_sec
FROM tire_stints ts
JOIN lap_times   lt ON lt.race_id   = ts.race_id
                    AND lt.driver_id = ts.driver_id
                    AND lt.lap_number BETWEEN ts.start_lap AND ts.end_lap
                    AND lt.is_pit_lap = 0            -- exclude in/out laps
JOIN drivers d  ON d.driver_id = ts.driver_id
JOIN races   r  ON r.race_id   = ts.race_id
WHERE ts.race_id = ?1
GROUP BY ts.race_id, ts.driver_id, ts.compound
ORDER BY d.full_name, ts.stint_number;


-- ------------------------------------------------------------
-- Q2: Pit stop timing impact — position gained/lost
-- ------------------------------------------------------------
-- Compares a driver's race position just before vs just after
-- each pit stop to quantify the cost & undercut/overcut effect
-- Usage: pass ?1 = race_id
-- ------------------------------------------------------------
SELECT
    r.grand_prix,
    d.full_name                          AS driver,
    ps.stop_number,
    ps.lap                               AS pit_lap,
    ps.tire_compound                     AS new_compound,
    ROUND(ps.duration_ms / 1000.0, 2)   AS pit_duration_sec,
    pre.position                         AS position_before_pit,
    post.position                        AS position_after_pit,
    (pre.position - post.position)       AS positions_gained   -- positive = gained
FROM pit_stops ps
JOIN races   r   ON r.race_id   = ps.race_id
JOIN drivers d   ON d.driver_id = ps.driver_id
LEFT JOIN lap_times pre  ON pre.race_id    = ps.race_id
                         AND pre.driver_id  = ps.driver_id
                         AND pre.lap_number = ps.lap - 1
LEFT JOIN lap_times post ON post.race_id   = ps.race_id
                         AND post.driver_id = ps.driver_id
                         AND post.lap_number = ps.lap + 1
WHERE ps.race_id = ?1
ORDER BY d.full_name, ps.stop_number;


-- ------------------------------------------------------------
-- Q3: Tire degradation curve — lap-by-lap delta to best lap
-- ------------------------------------------------------------
-- For each stint, shows how much slower each successive lap is
-- vs the best lap of that stint (degradation proxy)
-- Usage: pass ?1 = race_id, ?2 = driver_id
-- ------------------------------------------------------------
SELECT
    ts.compound,
    ts.stint_number,
    lt.lap_number,
    (lt.lap_number - ts.start_lap + 1)      AS lap_in_stint,
    ROUND(lt.lap_time_ms / 1000.0, 3)       AS lap_time_sec,
    ROUND(
        (lt.lap_time_ms - MIN(lt.lap_time_ms)
            OVER (PARTITION BY ts.stint_id)) / 1000.0,
        3
    )                                        AS delta_to_best_sec
FROM tire_stints ts
JOIN lap_times lt ON lt.race_id    = ts.race_id
                  AND lt.driver_id  = ts.driver_id
                  AND lt.lap_number BETWEEN ts.start_lap AND ts.end_lap
                  AND lt.is_pit_lap = 0
WHERE ts.race_id = ?1
  AND ts.driver_id = ?2
ORDER BY ts.stint_number, lt.lap_number;


-- ------------------------------------------------------------
-- Q4: Strategy comparison — 1-stop vs 2-stop outcomes
-- ------------------------------------------------------------
-- Aggregates finishing positions grouped by number of pit stops
-- to show which strategy worked better in each race
-- Usage: pass ?1 = race_id
-- ------------------------------------------------------------
SELECT
    r.grand_prix,
    stops_summary.num_stops,
    COUNT(*)                            AS num_drivers,
    ROUND(AVG(rr.finish_position), 1)   AS avg_finish_pos,
    MIN(rr.finish_position)             AS best_finish,
    MAX(rr.finish_position)             AS worst_finish
FROM (
    SELECT race_id, driver_id, COUNT(*) AS num_stops
    FROM pit_stops
    WHERE race_id = ?1
    GROUP BY race_id, driver_id
) stops_summary
JOIN race_results rr ON rr.race_id   = stops_summary.race_id
                     AND rr.driver_id = stops_summary.driver_id
                     AND rr.status    = 'Finished'
JOIN races r         ON r.race_id    = stops_summary.race_id
GROUP BY stops_summary.num_stops
ORDER BY stops_summary.num_stops;


-- ------------------------------------------------------------
-- Q5: Undercut effectiveness — did pitting first pay off?
-- ------------------------------------------------------------
-- For pairs of drivers on track, checks if the driver who
-- pitted first ended up ahead of their rival after the stops
-- Usage: pass ?1 = race_id
-- ------------------------------------------------------------
WITH first_stops AS (
    SELECT
        race_id,
        driver_id,
        MIN(lap) AS first_pit_lap
    FROM pit_stops
    GROUP BY race_id, driver_id
)
SELECT
    r.grand_prix,
    d1.full_name                   AS driver_pitted_first,
    d2.full_name                   AS driver_pitted_later,
    fs1.first_pit_lap              AS first_pitted_on_lap,
    fs2.first_pit_lap              AS second_pitted_on_lap,
    rr1.finish_position            AS first_pitter_finish,
    rr2.finish_position            AS second_pitter_finish,
    CASE
        WHEN rr1.finish_position < rr2.finish_position THEN 'Undercut Worked'
        ELSE 'Undercut Failed'
    END                            AS undercut_result
FROM first_stops fs1
JOIN first_stops fs2 ON fs2.race_id = fs1.race_id
                     AND fs2.driver_id != fs1.driver_id
                     AND fs2.first_pit_lap > fs1.first_pit_lap
JOIN race_results rr1 ON rr1.race_id   = fs1.race_id
                      AND rr1.driver_id = fs1.driver_id
JOIN race_results rr2 ON rr2.race_id   = fs2.race_id
                      AND rr2.driver_id = fs2.driver_id
JOIN drivers d1 ON d1.driver_id = fs1.driver_id
JOIN drivers d2 ON d2.driver_id = fs2.driver_id
JOIN races   r  ON r.race_id    = fs1.race_id
WHERE fs1.race_id = ?1
  AND rr1.status = 'Finished'
  AND rr2.status = 'Finished'
ORDER BY fs1.first_pit_lap;
