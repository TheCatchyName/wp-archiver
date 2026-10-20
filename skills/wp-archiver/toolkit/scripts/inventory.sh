#!/usr/bin/env bash
# Read-only DB inventory for phase 06: table sizes, posts by type, big postmeta, options by prefix family,
# credential-looking options (values masked), users, comments, taxonomies.
#   bash scripts/inventory.sh
# Run it BEFORE writing scripts/scrub.sql's PER-SITE sections; it changes nothing.
set -euo pipefail
cd "$(dirname "$0")/.."
PREFIX=$(docker compose exec -T wordpress sh -c 'printf %s "$WORDPRESS_TABLE_PREFIX"')
sed -e "s/{P}/$PREFIX/g" scripts/inventory.sql \
  | docker compose exec -T db sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE" 2>&1' \
  | grep -v 'Using a password'
