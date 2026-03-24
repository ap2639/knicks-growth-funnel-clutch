# Knicks Analytics Dashboard

Generate the standalone dashboard:

```bash
./.venv/bin/python src/04_build_dashboard.py
```

Then open:

- `dashboard/index.html`

The page is fully self-contained and is built from the processed CSVs in `data/processed`.

## Visual assets

The dashboard already includes original inline SVG artwork for:

- a New York City skyline
- a Statue of Liberty silhouette

If you want to show an official Knicks logo too, add one of these files to `dashboard/assets/`:

- `knicks-logo.svg`
- `knicks-logo.png`
- `knicks-logo.webp`
- `knicks-logo.jpg`

After adding the file, rebuild:

```bash
./.venv/bin/python src/04_build_dashboard.py
```

The dashboard will automatically render the logo in the hero section.
