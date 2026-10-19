-- DB scrub for the archived site. Run through scripts/scrub.sh, which substitutes {P} (table prefix), {ADMIN} (local
-- admin login from .env), {THEME} (ACTIVE_THEME) and {DOMAIN} (placeholder-email domain) and takes a backup first.
-- Safe to re-run. Sections 1-5 and 6a are generic WordPress and run as-is. Sections marked PER-SITE ship as COMMENTED
-- EXAMPLES: write them from the inventory queries in phase 06 (DB-2: group options by prefix, decide per family).
-- A statement that errors stops the run -- use DROP TABLE IF EXISTS, never TRUNCATE/DELETE on a table that may not exist.

-- ---------------------------------------------------------------- 1. disposable posts (generic)
DELETE FROM {P}posts WHERE post_type = 'revision';
DELETE FROM {P}posts WHERE post_status IN ('auto-draft', 'trash');
DELETE FROM {P}posts WHERE post_type = 'oembed_cache';
-- PER-SITE examples: form-plugin definitions, gallery display types, the default draft privacy page, stale copies of a
-- theme's custom CSS (keep only the post theme_mods_{THEME} points at: `wp option get theme_mods_{THEME}` -> custom_css_post_id).
-- DELETE FROM {P}posts WHERE post_type IN ('example_form', 'example_gallery_type');
-- DELETE FROM {P}posts WHERE post_type = 'page' AND post_status = 'draft' AND post_name = 'privacy-policy';
-- UPDATE {P}options SET option_value = '0' WHERE option_name = 'wp_page_for_privacy_policy';
-- DELETE FROM {P}posts WHERE post_type = 'custom_css' AND ID <> 123;

-- ---------------------------------------------------------------- 2. orphans left by the deletes (generic)
DELETE pm FROM {P}postmeta pm LEFT JOIN {P}posts p ON p.ID = pm.post_id WHERE p.ID IS NULL;
DELETE tr FROM {P}term_relationships tr LEFT JOIN {P}posts p ON p.ID = tr.object_id WHERE p.ID IS NULL AND tr.object_id NOT IN (SELECT link_id FROM {P}links);
DELETE c FROM {P}comments c LEFT JOIN {P}posts p ON p.ID = c.comment_post_ID WHERE p.ID IS NULL;

-- ---------------------------------------------------------------- 3. regenerable per-post caches
DELETE FROM {P}postmeta WHERE meta_key IN ('_edit_lock',
   -- builder: Elementor (a no-op on other sites)
   '_elementor_css', '_elementor_element_cache', '_elementor_controls_usage'
   -- PER-SITE: other plugins' bookkeeping meta keys, e.g. , '_example_plugin_cache'
   );

-- ---------------------------------------------------------------- 4. comments: keep approved ones, drop all PII
DELETE FROM {P}comments WHERE NOT (comment_approved = '1' AND comment_type = 'comment');
UPDATE {P}comments SET comment_author_email = '', comment_author_IP = '', comment_agent = '';
DELETE cm FROM {P}commentmeta cm LEFT JOIN {P}comments c ON c.comment_ID = cm.comment_id WHERE c.comment_ID IS NULL;
UPDATE {P}posts p SET comment_count = (SELECT COUNT(*) FROM {P}comments c WHERE c.comment_post_ID = p.ID AND c.comment_approved = '1');

-- ---------------------------------------------------------------- 5. users: no credentials, no real addresses
-- The local admin is recreated by setup.sh from .env, so it never goes into the seed.
DELETE um FROM {P}usermeta um JOIN {P}users u ON u.ID = um.user_id WHERE u.user_login = '{ADMIN}';
DELETE FROM {P}users WHERE user_login = '{ADMIN}';
UPDATE {P}users SET user_pass = '!scrubbed-no-login', user_activation_key = '', user_email = CONCAT(user_login, '@{DOMAIN}');
DELETE FROM {P}usermeta WHERE meta_key IN ('session_tokens', 'community-events-location', 'dismissed_wp_pointers');
DELETE um FROM {P}usermeta um LEFT JOIN {P}users u ON u.ID = um.user_id WHERE u.ID IS NULL;
UPDATE {P}options SET option_value = 'admin@{DOMAIN}' WHERE option_name IN ('admin_email', 'new_admin_email');

-- ---------------------------------------------------------------- 6. options
-- 6a. caches and transients (generic)
DELETE FROM {P}options WHERE option_name LIKE '\_transient\_%' OR option_name LIKE '\_site\_transient\_%';
DELETE FROM {P}options WHERE option_name IN ('cron', 'recently_activated', 'recovery_keys', 'admin_email_lifespan',
  -- builder: Elementor caches/logs (a no-op on other sites)
  'elementor_log', 'elementor_remote_info_library', 'elementor_controls_usage', '_elementor_assets_data',
  '_elementor_global_css', '_elementor_element_cache_unique_id',
  -- builder: Divi cache (regenerated on render; holds no settings; a no-op on other sites)
  '_et_builder_da_feature_cache',
  -- builder: Divi licence credentials and support-site ids: `et_automatic_updates_options` holds the owner's Elegant
  -- Themes username + API key. A secret: never let it reach the seed (DB-4). A no-op on other sites.
  'et_automatic_updates_options', 'et_support_site_id', 'et-support-center-safe-mode-verify', 'et_account_status');
DELETE FROM {P}usermeta WHERE meta_key LIKE '\_et\_support\_center%';   -- builder: Divi (a no-op elsewhere)
-- NOT deleted, builder: Divi -- options `et_divi`, `et_pb_*` (incl. per-form `et_pb_contact_form_*`), `et_google_api_settings` and
-- post meta `_et_pb_*`, `_et_builder_*`, `_global_colors_info`: settings or registries the render may depend on (DB-2).
-- NOT deleted, builder: Elementor -- `_elementor_local_google_fonts`. It is the registry of self-hosted fonts, not a
-- cache; without it Elementor falls back to Google's CDN (and cannot re-download: outbound HTTP is blocked). DB-2.

-- 6b. PER-SITE: settings, keys, logs and caches of plugins/hosting that were removed. Inventory first:
--   SELECT SUBSTRING_INDEX(TRIM(LEADING '_' FROM option_name),'_',1) AS family, COUNT(*), SUM(LENGTH(option_value))
--   FROM {P}options GROUP BY family ORDER BY 3 DESC;
-- Typical offenders: login-attempt logs (visitor IPs), backup/management-plugin keys, licence tokens, account
-- registries (Freemius `fs_*`), analytics settings, host-helper plugins. Keep registries; delete caches/logs/keys.
-- DELETE FROM {P}options WHERE
--      option_name LIKE 'example\_plugin%'
--   OR (option_name LIKE 'theme\_mods\_%' AND option_name <> 'theme_mods_{THEME}');   -- other themes' customiser data

-- ---------------------------------------------------------------- 7. whole tables of removed plugins (PER-SITE)
-- `wp plugin delete` runs uninstall hooks but leaves tables behind (PRN-2): that list is your drop list.
--   SELECT table_name, ROUND((data_length+index_length)/1048576,2) AS mb FROM information_schema.tables
--   WHERE table_schema = DATABASE() ORDER BY mb DESC;
-- DROP TABLE IF EXISTS {P}example_plugin_log, {P}example_plugin_stats;
-- Tables of plugins that STAY installed are emptied, not dropped, and only when you know they exist:
-- TRUNCATE TABLE {P}example_events;
