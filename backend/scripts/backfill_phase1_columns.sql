BEGIN;

WITH q_base AS (
    SELECT
        id,
        COALESCE(difficulty, '') AS difficulty,
        reference_answer AS ref_json,
        COALESCE(reference_answer::text, '') AS ref_text
    FROM questions
),
q_calc AS (
    SELECT
        id,
        difficulty,
        CASE
            WHEN jsonb_typeof(ref_json) = 'array' THEN GREATEST(1, jsonb_array_length(ref_json))
            ELSE GREATEST(
                1,
                regexp_count(ref_text, E'(^|\\n)\\s*(-|\\*|\\d+[\\.)])\\s+') + 1,
                regexp_count(ref_text, E'[。.!?;；]+') + 1
            )
        END AS point_cnt
    FROM q_base
),
q_depth AS (
    SELECT
        id,
        CASE
            WHEN difficulty = 'hard' AND point_cnt >= 3 THEN 3
            WHEN difficulty = 'medium' AND point_cnt >= 5 THEN 3
            WHEN point_cnt >= 7 THEN 3
            WHEN difficulty = 'hard' OR point_cnt >= 3 THEN 2
            ELSE 1
        END AS depth
    FROM q_calc
)
UPDATE questions q
SET reference_answer_depth = d.depth
FROM q_depth d
WHERE q.id = d.id;

WITH q_calc AS (
    SELECT
        id,
        COALESCE(difficulty, '') AS difficulty,
        COALESCE(keywords, '[]'::jsonb) AS kws
    FROM questions
)
UPDATE questions q
SET required_skills_meta = jsonb_build_object(
    'required_skills', q_calc.kws,
    'minimum_mastery',
    CASE
        WHEN q_calc.difficulty = 'hard' THEN 70
        WHEN q_calc.difficulty = 'medium' THEN 60
        ELSE 50
    END,
    'difficulty', q_calc.difficulty
)
FROM q_calc
WHERE q.id = q_calc.id
  AND q.required_skills_meta IS NULL;

WITH q_calc AS (
    SELECT
        id,
        COALESCE(keywords ->> 0, '该知识点') AS k0
    FROM questions
)
UPDATE questions q
SET follow_up_templates = jsonb_build_array(
    jsonb_build_object(
        'condition', 'answer_incomplete',
        'text', 'You mentioned ' || q_calc.k0 || ', but the answer is incomplete. Please explain core principles, boundaries, and one real project example.'
    )
)
FROM q_calc
WHERE q.id = q_calc.id
  AND q.follow_up_templates IS NULL;

WITH rt AS (
        SELECT resource_id, MIN(tag_id) AS tag_id
        FROM resource_tags
        GROUP BY resource_id
)
UPDATE resources r
SET tag_id = rt.tag_id
FROM rt
WHERE r.id = rt.resource_id
    AND r.tag_id IS NULL;

COMMIT;
