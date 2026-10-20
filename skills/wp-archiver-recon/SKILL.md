---
name: wp-archiver-recon
description: Read-only survey of a live WordPress site from outside — is it a good candidate to archive as a static site? Detects theme, page builder, plugins, forms, third-party hosts, content counts and old domains, then classifies candidate or not. Use to triage, assess, audit or "check" a WordPress site before archiving or migrating it; no Docker or repo needed.
---

# wp-archiver-recon

Phase 01 of the `wp-archiver` workflow, standalone. Everything here is a read-only GET against a public URL: nothing is installed, logged into or changed. Run it against a site the user owns or is authorised to assess.

## Steps

Set `B=https://<site>` (the live or temp URL). Use `curl -k` for read-only recon: temp hosts often have bad certificates (RST-1).

```
curl -sSk -L -o home.html -w "%{http_code} %{size_download}\n" $B/
grep -oE '/wp-content/(plugins|themes)/[^/"]+' home.html | sort | uniq -c | sort -rn      # plugins + theme visible in markup
grep -oiE '<meta name="generator"[^>]*>' home.html                                         # WordPress + page builder versions
grep -oE 'https?://[^"'"'"' )\\]+' home.html | grep -v <host> | sed -E 's#(https?://[^/]+).*#\1#' | sort | uniq -c | sort -rn   # third parties
curl -sk $B/wp-sitemap.xml; curl -sk $B/robots.txt
curl -sk "$B/wp-json/wp/v2/pages?per_page=100&_fields=id,slug,link,title"                 # page list
curl -skI "$B/wp-json/wp/v2/posts?per_page=1" | grep -i x-wp-total                         # counts (also media, other types)
grep -oE '<form[^>]*>|<iframe[^>]*>' home.html; grep -oE 'elementor-widget-[a-z-]+' home.html | sort | uniq -c | sort -rn
```

Also fetch the contact page and any page that looks interactive; note the form plugin, counters/analytics, comment forms, search, embeds, and hard-coded links to old domains (`grep -o 'http://old-domain'`). REST may be disabled or locked down: fall back to the sitemap and the nav links, and say that counts are partial.

## Identify the page builder

The builder decides which adapter applies (`wp-archiver`'s `builders/`). From the home page HTML and public theme/plugin files:

| Builder | Signals | Version |
|---|---|---|
| Elementor | `<meta name="generator" content="Elementor x.y.z">`, `elementor-widget-*` classes, `/wp-content/plugins/elementor/` | the generator meta |
| Divi (a **theme**: plugins may be empty) | `/wp-content/themes/Divi/` in asset URLs, `et_pb_*` and `et-boc` classes, Theme Builder regions `..._tb_header` / `..._tb_footer`; the generator meta names only WordPress | `curl -s $B/wp-content/themes/Divi/style.css` and read its `Version:` line (4.x proven; 5 untested) |
| Block theme / plain | `wp-block-*` classes, no builder folder | n/a: no adapter needed |
| Anything else (Beaver, WPBakery, Bricks, Oxygen) | its folder under `/wp-content/plugins` or `/themes` | no adapter yet: say so |

Also note, because they decide work later: viewport-sized sections (`min-height: 90vh`, hero sliders) mean screenshots need the viewport-preserving capture (VIS-8); a premium builder or theme (Elegant Themes, etc.) means licence-bound code that cannot be re-downloaded (ARC-3); count `et_pb_contact_form` and form plugins as dynamic features to replace.

## Classify

- **Candidate:** no logins, shop, member areas or site search; at most forms (drop or replace with a notice) and trackers (drop).
- **Not a candidate:** WooCommerce, memberships, LMS, bookings — anything where visitors change data. Stop and say so.
- **Borderline:** comments, newsletters, maps with API keys, embedded third-party apps. List each with a drop / replace / keep-as-third-party option for the owner.

## Report

Write the findings in one note (a `docs/RECON.md` or the reply) with: page / post / media counts · WordPress version · theme and page builder (+ versions) · visible plugins · dynamic features and the proposed handling · third-party hosts · old domains and temp hosts · anything unverifiable from outside (hidden plugins, server-side behaviour). Then give a verdict: candidate / not / borderline, and what the owner must decide. Name the builder explicitly; if it is not Elementor, say that `wp-archiver`'s builder adapter for it does not exist yet (`builders/README.md`).

## Done when
You can list: counts, theme + builder, visible plugins, dynamic features, third-party hosts and old domains, and the owner has the verdict. To continue, hand off to the `wp-archiver` skill at phase 02 (capture).
