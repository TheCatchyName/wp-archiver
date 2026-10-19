#!/bin/sh
# Runs inside the wpcli container, after the stack is up:
#
#   docker compose --profile tools run --rm wpcli sh setup.sh
#
# Idempotent: points the imported database at http://localhost, rewrites the old hosts (OLD_HOSTS in .env),
# keeps search engines out, and creates/updates a local admin from .env (WP_ADMIN_USER / _EMAIL / _PASSWORD).
set -eu

SITE_URL="http://localhost"
WP="wp --path=/var/www/html"

echo "waiting for WordPress..."
i=0
until $WP core is-installed 2>/dev/null; do
  i=$((i + 1)); [ "$i" -gt 60 ] && { echo "WordPress never came up"; exit 1; }
  sleep 2
done

[ -n "${OLD_HOSTS:-}" ] || echo "WARNING: OLD_HOSTS is empty -- no old host will be rewritten (set it in .env)"

# Old origins baked into content, in both plain and JSON-escaped (page builders store \/ in their JSON) forms.
esc_new=$(printf '%s' "$SITE_URL" | sed 's#/#\\/#g')
for host in ${OLD_HOSTS:-}; do
  for scheme in http https; do
    old="$scheme://$host"
    esc_old=$(printf '%s' "$old" | sed 's#/#\\/#g')
    $WP search-replace "$old" "$SITE_URL" --all-tables-with-prefix --skip-columns=guid --report-changed-only
    $WP search-replace "$esc_old" "$esc_new" --all-tables-with-prefix --skip-columns=guid --report-changed-only
  done
done

# BUILDER=elementor: Elementor's self-hosted Google-font CSS files hard-code absolute URLs to the old host inside
# the files themselves (search-replace only touches the database): rewrite them too, or the fonts silently fail (RST-6).
FONT_CSS=/var/www/html/wp-content/uploads/elementor/google-fonts/css
if [ -d "$FONT_CSS" ]; then
  for host in ${OLD_HOSTS:-}; do
    for scheme in http https; do
      sed -i "s#$scheme://$host#$SITE_URL#g" "$FONT_CSS"/*.css
    done
  done
fi

$WP option update home "$SITE_URL"
$WP option update siteurl "$SITE_URL"
$WP option update blog_public 0

if $WP plugin is-active elementor 2>/dev/null; then
  $WP elementor flush-css || true
fi
$WP rewrite flush --hard 2>/dev/null || $WP rewrite flush

# Our own local admin, driven by .env. Imported users (the site's own logins) are left untouched.
if $WP user get "$WP_ADMIN_USER" >/dev/null 2>&1; then
  $WP user update "$WP_ADMIN_USER" --user_pass="$WP_ADMIN_PASSWORD" --role=administrator --skip-email
else
  $WP user create "$WP_ADMIN_USER" "$WP_ADMIN_EMAIL" --role=administrator --user_pass="$WP_ADMIN_PASSWORD"
fi
echo "site: $SITE_URL   admin: $SITE_URL/wp-admin/   login: $WP_ADMIN_USER (password: WP_ADMIN_PASSWORD in .env)"
