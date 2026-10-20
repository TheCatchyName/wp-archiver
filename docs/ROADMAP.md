# Roadmap and open items

Not promises: the gaps the reference run and this extraction left open, in rough priority order.

1. ~~Second-site trial of the generalised toolkit~~ - done (Divi, 2026-10-19, deployed). A **third** site with another builder, theme or host is the next real test.
2. **Builder adapters** beyond Elementor and Divi (`skills/wp-archiver/builders/`; `apply.sh` installs them). Each needs: runtime-asset list, out-of-DB absolute URLs, cache flush, scrub entries, head cruft, image behaviour, licensing notes.
3. **Remote baseline** so unused plugins can be trimmed on the live host *before* capture: adapt `snapshot.sh` to a sitemap / REST URL list.
4. **`plugins.lock` installer** (`wp plugin install <slug> --version=<v>`) so `.data/html` is fully disposable and the stack rebuilds from the repo alone.
5. **Named volume for `.data/html`** to remove the bind-mount slowness on Windows/macOS (ENV-8).
6. **macOS / Linux pass** over the toolkit: venv path detection is in, port 80 and browser discovery are untested.
7. **Cloudflare Pages/Workers drift check**: the publish phase tells the agent to re-read the docs; consider a small script that diffs `wrangler.jsonc` against the current schema.
8. **Automated smoke test** of the toolkit against a tiny synthetic WordPress seed, so regressions show up without a real site. (The generalisation was checked by hand: rebuild a known site from its scrubbed seed and diff the output against the original; that procedure is the starting point.)
9. ~~Re-test the pixel-diff harness after the generalisation~~ — done on the second site; it needed a new capture mode (VIS-8).
10. **Divi follow-ups:** slider/video interaction checks, **Divi 5**, a larger site; which `_et_*` post meta the scrub can drop.
