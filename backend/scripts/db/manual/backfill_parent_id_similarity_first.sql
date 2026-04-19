BEGIN;

UPDATE knowledge_tags k
SET parent_id = b.parent_id
FROM knowledge_tags_parent_backup_20260410 b
WHERE b.id = k.id;

WITH parent_tags AS (
    SELECT id, name
    FROM knowledge_tags
    WHERE NOT (category IS NULL OR category = '')
),
child_tags AS (
    SELECT id, name
    FROM knowledge_tags
    WHERE (category IS NULL OR category = '')
),
child_question AS (
    SELECT c.id AS child_id, q.id AS question_id, q.job_id
    FROM child_tags c
    JOIN questions q ON q.reference_answer::text LIKE ('%' || c.name || '%')
),
direct_q_pairs AS (
    SELECT
        c.id AS child_id,
        p.id AS parent_id,
        COUNT(*) AS hit_cnt,
        MAX(similarity(kw.value, p.name)) AS kw_sim,
        MIN(char_length(p.name)) AS parent_name_len
    FROM child_tags c
    JOIN questions q ON q.reference_answer::text LIKE ('%' || c.name || '%')
    JOIN LATERAL jsonb_array_elements_text(q.keywords) kw(value) ON TRUE
    JOIN parent_tags p ON p.name ILIKE ('%' || kw.value || '%')
    GROUP BY c.id, p.id
),
direct_ranked AS (
    SELECT
        child_id,
        parent_id,
        ROW_NUMBER() OVER (
            PARTITION BY child_id
            ORDER BY hit_cnt DESC, kw_sim DESC, parent_name_len ASC, parent_id ASC
        ) AS rn
    FROM direct_q_pairs
),
direct_best AS (
    SELECT child_id, parent_id
    FROM direct_ranked
    WHERE rn = 1
),
parent_job_counts AS (
    SELECT d.parent_id, cq.job_id, COUNT(*) AS cnt
    FROM direct_best d
    JOIN child_question cq ON cq.child_id = d.child_id
    GROUP BY d.parent_id, cq.job_id
),
parent_job_best AS (
    SELECT
        parent_id,
        job_id,
        ROW_NUMBER() OVER (PARTITION BY parent_id ORDER BY cnt DESC, job_id ASC) AS rn
    FROM parent_job_counts
),
parent_job AS (
    SELECT parent_id, job_id
    FROM parent_job_best
    WHERE rn = 1
),
child_job_counts AS (
    SELECT child_id, job_id, COUNT(*) AS cnt
    FROM child_question
    GROUP BY child_id, job_id
),
child_job_best AS (
    SELECT
        child_id,
        job_id,
        ROW_NUMBER() OVER (PARTITION BY child_id ORDER BY cnt DESC, job_id ASC) AS rn
    FROM child_job_counts
),
child_job AS (
    SELECT child_id, job_id
    FROM child_job_best
    WHERE rn = 1
),
kw_parent_counts AS (
    SELECT
        cq.job_id,
        kw.value AS kw,
        d.parent_id,
        COUNT(*) AS cnt
    FROM direct_best d
    JOIN child_question cq ON cq.child_id = d.child_id
    JOIN questions q ON q.id = cq.question_id
    JOIN LATERAL jsonb_array_elements_text(q.keywords) kw(value) ON TRUE
    GROUP BY cq.job_id, kw.value, d.parent_id
),
kw_parent_best AS (
    SELECT
        job_id,
        kw,
        parent_id,
        ROW_NUMBER() OVER (PARTITION BY job_id, kw ORDER BY cnt DESC, parent_id ASC) AS rn
    FROM kw_parent_counts
),
kw_map AS (
    SELECT job_id, kw, parent_id
    FROM kw_parent_best
    WHERE rn = 1
),
fallback_pairs AS (
    SELECT
        c.id AS child_id,
        km.parent_id,
        COUNT(*) AS hit_cnt
    FROM child_tags c
    JOIN questions q ON q.reference_answer::text LIKE ('%' || c.name || '%')
    JOIN LATERAL jsonb_array_elements_text(q.keywords) kw(value) ON TRUE
    JOIN kw_map km ON km.kw = kw.value AND km.job_id = q.job_id
    WHERE c.id NOT IN (SELECT child_id FROM direct_best)
    GROUP BY c.id, km.parent_id
),
fallback_ranked AS (
    SELECT
        child_id,
        parent_id,
        ROW_NUMBER() OVER (PARTITION BY child_id ORDER BY hit_cnt DESC, parent_id ASC) AS rn
    FROM fallback_pairs
),
fallback_best AS (
    SELECT child_id, parent_id
    FROM fallback_ranked
    WHERE rn = 1
),
trigram_pairs AS (
    SELECT
        c.id AS child_id,
        p.id AS parent_id,
        ROW_NUMBER() OVER (
            PARTITION BY c.id
            ORDER BY similarity(c.name, p.name) DESC, p.id ASC
        ) AS rn
    FROM child_tags c
    JOIN child_job cj ON cj.child_id = c.id
    JOIN parent_job pj ON pj.job_id = cj.job_id
    JOIN parent_tags p ON p.id = pj.parent_id
    WHERE c.id NOT IN (
        SELECT child_id FROM direct_best
        UNION
        SELECT child_id FROM fallback_best
    )
),
trigram_best AS (
    SELECT child_id, parent_id
    FROM trigram_pairs
    WHERE rn = 1
),
global_missing AS (
    SELECT
        c.id AS child_id,
        p.id AS parent_id,
        ROW_NUMBER() OVER (
            PARTITION BY c.id
            ORDER BY similarity(c.name, p.name) DESC, p.id ASC
        ) AS rn
    FROM child_tags c
    CROSS JOIN parent_tags p
    WHERE c.id NOT IN (
        SELECT child_id FROM direct_best
        UNION
        SELECT child_id FROM fallback_best
        UNION
        SELECT child_id FROM trigram_best
    )
),
global_best AS (
    SELECT child_id, parent_id
    FROM global_missing
    WHERE rn = 1
),
combined AS (
    SELECT * FROM direct_best
    UNION ALL
    SELECT * FROM fallback_best
    UNION ALL
    SELECT * FROM trigram_best
    UNION ALL
    SELECT * FROM global_best
)
UPDATE knowledge_tags kt
SET parent_id = c.parent_id
FROM combined c
WHERE kt.id = c.child_id;

COMMIT;
