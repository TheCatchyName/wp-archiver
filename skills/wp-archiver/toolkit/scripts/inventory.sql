-- Read-only database inventory: what to decide before writing scrub.sql's PER-SITE sections (phase 06).
-- Run through scripts/inventory.sh, which substitutes {P} (the table prefix). Changes nothing.
SET SESSION information_schema_stats_expiry=0;

SELECT '== table sizes (MB): leftovers of removed plugins show up here, with their own prefixes' AS '';
SELECT table_name, table_rows, ROUND((data_length+index_length)/1048576,2) AS mb
FROM information_schema.tables WHERE table_schema = DATABASE() ORDER BY mb DESC;

SELECT '== posts by type/status: revisions, auto-drafts, builder library/layout types' AS '';
SELECT post_type, post_status, COUNT(*) AS n FROM {P}posts GROUP BY 1,2 ORDER BY n DESC;

SELECT '== largest postmeta keys: caches (delete) vs settings (keep)' AS '';
SELECT meta_key, COUNT(*) AS n, ROUND(SUM(LENGTH(meta_value))/1024,1) AS kb
FROM {P}postmeta GROUP BY meta_key ORDER BY kb DESC LIMIT 25;

SELECT '== options grouped by prefix family: decide per family (DB-2)' AS '';
SELECT SUBSTRING_INDEX(TRIM(LEADING '_' FROM option_name),'_',1) AS family, COUNT(*) AS n, ROUND(SUM(LENGTH(option_value))/1024,1) AS kb
FROM {P}options GROUP BY family ORDER BY kb DESC LIMIT 40;

SELECT '== options whose value looks like a credential (names only; values masked)' AS '';
-- Masking: quoted strings of 9+ chars and any bare run of 16+ token characters (JWTs, base64 key bodies, hashes) are hidden,
-- so the output shows structure and names only and is safe to read into a transcript (ENV-5).
SELECT option_name,
       REGEXP_REPLACE(REGEXP_REPLACE(LEFT(option_value, 120), '"[^"]{9,}"', '"<masked>"'), '[A-Za-z0-9+/=_.-]{16,}', '<masked>') AS shape
FROM {P}options
WHERE option_name REGEXP '(api|license|licence|secret|token|password|passwd|private|client_key|service_key|access_key)'
   OR option_value REGEXP '"(api_key|apikey|username|password|secret|token)"'
ORDER BY option_name;

SELECT '== users (hash type and email start only)' AS '';
SELECT ID, user_login, LEFT(user_email, 3) AS email_start, LEFT(user_pass, 4) AS pass_start FROM {P}users;

SELECT '== usermeta keys' AS '';
SELECT meta_key, COUNT(*) AS n FROM {P}usermeta GROUP BY meta_key ORDER BY n DESC;

SELECT '== comments' AS '';
SELECT comment_approved, comment_type, COUNT(*) AS n FROM {P}comments GROUP BY 1,2;

SELECT '== taxonomies (a removed plugin may leave its own)' AS '';
SELECT taxonomy, COUNT(*) AS n FROM {P}term_taxonomy GROUP BY taxonomy ORDER BY n DESC;
