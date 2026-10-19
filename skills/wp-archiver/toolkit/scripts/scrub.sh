#!/usr/bin/env bash
# Scrub the local database, optionally dump it as the tracked seed, then recreate the local admin.
#   bash scripts/scrub.sh            # scrub only
#   bash scripts/scrub.sh --seed     # ... and write db/seed.sql (the scrubbed, committable seed)
# Takes a full backup first (.data/backup/, gitignored). Per-site lists live in scrub.sql.
#
# Order matters (DB-1): nothing may boot WordPress (WP-CLI, a page view) between the scrub and the seed dump,
# or plugins re-create their own option rows (licence/account records, export keys) inside the seed.
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; . ./.env; set +a
: "${DB_NAME:?}" "${ACTIVE_THEME:?}" "${COMPOSE_PROJECT_NAME:?}"
DB="docker compose exec -T db sh -c"
MYSQL='mysql -uroot -p"$MYSQL_ROOT_PASSWORD" '"$DB_NAME"
DUMPER='mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" --single-transaction --no-tablespaces'
PREFIX=$(docker compose exec -T wordpress sh -c 'printf %s "$WORDPRESS_TABLE_PREFIX"')
ADMIN="${WP_ADMIN_USER:-localadmin}"
mkdir -p .data/backup
STAMP=$(date +%Y%m%d-%H%M%S)

# MySQL 8 caches table statistics for 24h; expiry=0 makes information_schema report the truth (ENV-10).
size() { $DB "$MYSQL -N -e \"set session information_schema_stats_expiry=0; select round(sum(data_length+index_length)/1048576,1) from information_schema.tables where table_schema='$DB_NAME'\" 2>/dev/null" | tr -d '\r'; }
echo "DB size before: $(size) MB"
$DB "$DUMPER $DB_NAME 2>/dev/null" > ".data/backup/pre-scrub-$STAMP.sql"
echo "backup: .data/backup/pre-scrub-$STAMP.sql"

sed -e "s/{P}/$PREFIX/g" -e "s/{ADMIN}/$ADMIN/g" -e "s/{THEME}/$ACTIVE_THEME/g" -e "s/{DOMAIN}/$COMPOSE_PROJECT_NAME.test/g" scripts/scrub.sql \
  | $DB "$MYSQL 2>&1" | grep -v 'Using a password' || true
TABLES=$($DB "$MYSQL -N -e \"select group_concat(table_name) from information_schema.tables where table_schema='$DB_NAME'\" 2>/dev/null" | tr -d '\r')
$DB "$MYSQL -e \"optimize table $TABLES\" >/dev/null 2>&1" || true   # InnoDB only gives space back after a rebuild
echo "DB size after:  $(size) MB"

if [ "${1:-}" = "--seed" ]; then
  $DB "$DUMPER --skip-comments --skip-dump-date --skip-extended-insert --default-character-set=utf8mb4 $DB_NAME 2>/dev/null" > db/seed.sql
  echo "seed written: db/seed.sql ($(wc -c < db/seed.sql) bytes, $(wc -l < db/seed.sql) lines)"
fi

# Only now is it safe to boot WordPress. The scrub deleted the local admin so it can't reach the seed.
WPC="docker compose --profile tools run --rm wpcli wp"
$WPC cache flush 2>&1 | grep -E 'Success|Error' || true
docker compose --profile tools run --rm wpcli sh setup.sh 2>&1 | grep -E 'login:|Error' || true
