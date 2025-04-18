WITH RECURSIVE gd (idx, a, b) AS (
    SELECT 0, 1, 1
UNION ALL
    SELECT idx+1, a-rate*avg(2*x*(a*x+b-y)), b-rate*avg(2*(a*x+b-y))
    FROM gd, points, lr
    WHERE idx < 5 GROUP BY idx, a, b, rate
)
SELECT * FROM gd WHERE idx = 5;
