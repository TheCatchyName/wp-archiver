#!/usr/bin/env bash
# TEMPLATE -- write this from your own proof loop (phase 05), so the prune can be re-applied to a fresh restore:
#   bash scripts/prune.sh
# Every plugin named here must already have been shown unused by a render diff (scripts/check.sh). Survivors are
# recorded in docker/wordpress/plugins.lock.
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; . ./.env; set +a
WP="docker compose --profile tools run --rm wpcli wp"
q() { grep -vE 'Container|database error|^\s*$' || true; }

# 1. Replace any dead dynamic feature (a form) with its deliberate notice FIRST, while the plugin's widget type still
#    exists (PRN-1). Copy scripts/archive-form-notice.php.example to archive-form-notice.php and fill it in.
# $WP eval-file archive-form-notice.php 2>&1 | q

# 2. Plugins proven unused, in the batches you proved them (PRN-6): trackers/host helpers -> unused block libraries -> inactive.
# $WP plugin deactivate example-tracker example-host-helper 2>&1 | q
# $WP plugin delete example-tracker example-host-helper example-inactive-plugin 2>&1 | q

# 3. Unused default themes.
# $WP theme delete twentytwentyfive twentytwentyfour 2>&1 | q

# 4. Builder caches, search-engine stance, and a final listing.
if [ "${BUILDER:-}" = "elementor" ]; then $WP elementor flush-css 2>&1 | q; fi
$WP option update blog_public 0 2>&1 | q
$WP plugin list --fields=name,status,version --format=table 2>&1 | q
