# Website

A very small static website starter.

## Files

- `index.html` contains the page content.
- `styles.css` contains the visual styling.

Open `index.html` in a browser to view the site.

## Library Photos

1. Add raw book scans to `images/library/originals/`.
2. Run:

```bash
/Users/Kels/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 tools/process_library_images.py
```

The script exports cleaned images to `images/library/processed/` and updates `photos.js`.
