# Website

A very small static website starter.

## Files

- `index.html` contains the page content.
- `styles.css` contains the visual styling.

Open `index.html` in a browser to view the site.

## Library Photos

1. Add front cover scans to `images/library/originals/front/`.
2. Add optional matching back cover scans to `images/library/originals/back/`.
3. Use the same file name for the front and back cover pair. For example, `the-left-hand-of-darkness.jpg` in both folders.
4. Name each file the way you want its caption to appear. For example, `the-left-hand-of-darkness.jpg` becomes `The Left Hand Of Darkness`.
5. Run:

```bash
/Users/Kels/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 tools/process_library_images.py
```

The script exports cleaned images to `images/library/processed/` and updates `photos.js` with captions from the original file names. If a matching back cover exists, the site fades to it when the book is hovered or focused.
