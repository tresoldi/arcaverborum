# Arca Verborum Website Implementation Plan

## Overview

Create a simple, professional website for arcaverborum.org that:
- Presents dataset information and academic context
- Updates automatically at each release
- Uses Jinja2 templating (consistent with release system)
- Hosts on GitHub Pages (docs/ folder)
- Uses Uppsala University color scheme

## Design Specifications

### Color Scheme (Uppsala University)
- **Primary Red:** RGB(153, 0, 0) / #990000
- **Grey:** RGB(230, 230, 230) / #E6E6E6
- **White:** #FFFFFF
- **Black:** #000000

### Style
- Research/professional aesthetic
- Clean, modern, academic credibility
- Mobile-responsive
- Minimal CSS framework (Pico CSS) + custom Uppsala colors

## Site Structure

### Two-page design:

**1. index.html (Landing Page)**
- Hero section (title, tagline)
- Brief description (what is Arca Verborum)
- Collections overview (full/core/corecog cards)
- Download section (latest version via concept DOI)
- Citation section
- Contact/About section (inline, bottom of page)
- Links to GitHub, documentation

**2. datasets.html (Dataset Details)**
- Comprehensive statistics for all three collections
- Data quality metrics
- Collection comparison table
- Technical details
- Link back to landing page

## File Structure

```
arcaverborum/
├── docs/                          # GitHub Pages root
│   ├── index.html                # Generated landing page
│   ├── datasets.html             # Generated datasets page
│   ├── css/
│   │   ├── pico.min.css         # Minimal CSS framework
│   │   └── custom.css           # Uppsala colors + custom styles
│   └── .nojekyll                # Disable Jekyll processing
│
├── templates/
│   └── website/                  # NEW: Website templates
│       ├── base.html.j2         # Base layout (header, footer, styles)
│       ├── index.html.j2        # Landing page template
│       └── datasets.html.j2     # Datasets page template
│
└── prepare_release.py            # MODIFIED: Add build_website() function
```

## Template Context (Data Available to Templates)

```python
{
    # Version info
    'version': '20251002',
    'release_date': '2025-10-02',
    'year': 2025,

    # Full collection
    'full_datasets': 149,
    'full_forms': 2915515,
    'full_languages': 6234,
    'full_parameters': 5432,
    'full_cognate_datasets': 58,
    'full_doi_concept': '10.5281/zenodo.XXXXXXX',  # Concept DOI (latest)

    # Core collection
    'core_datasets': 13,
    'core_forms': 221459,
    'core_languages': 1617,
    'core_parameters': 2987,
    'core_cognate_datasets': 9,
    'core_doi_concept': '10.5281/zenodo.XXXXXXX',

    # CORECOG collection
    'corecog_datasets': 58,
    'corecog_forms': 183729,
    'corecog_languages': 1193,
    'corecog_parameters': 2887,
    'corecog_cognate_datasets': 8,
    'corecog_doi_concept': '10.5281/zenodo.XXXXXXX',

    # Quality metrics (from full collection)
    'glottolog_coverage': 95.0,
    'concepticon_coverage': 85.0,
    'cognate_coverage': 45.0,
    'segments_coverage': 78.0,

    # Links
    'github_url': 'https://github.com/tresoldi/arcaverborum',
    'github_releases': 'https://github.com/tresoldi/arcaverborum/releases',
    'zenodo_community': 'https://zenodo.org/communities/lexibank',
}
```

## Integration with Release Process

### Modified prepare_release.py workflow:

```python
def build_website(version: str, stats_full: dict, stats_core: dict, stats_corecog: dict):
    """
    Generate website from templates with latest statistics.

    Called at the end of prepare_release.py after archives are created.
    Reads validation reports, extracts statistics, renders templates to docs/
    """
    # 1. Extract statistics from validation reports
    # 2. Build template context
    # 3. Render base.html.j2, index.html.j2, datasets.html.j2
    # 4. Write to docs/index.html, docs/datasets.html
    # 5. Log success

# At end of main():
if not args.dry_run:
    build_website(version, stats_full, stats_core, stats_corecog)
    logger.info("Website generated in docs/")
```

## GitHub Pages Configuration

### Setup (one-time):
1. Repository Settings → Pages
2. Source: Deploy from a branch
3. Branch: master
4. Folder: /docs
5. Save

### Deployment:
- Automatic on push to master
- Website available at: https://tresoldi.github.io/arcaverborum/
- Custom domain (later): arcaverborum.org via CNAME file

## Design Elements

### Landing Page (index.html)

**Hero Section:**
- Large title: "Arca Verborum"
- Subtitle: "A Global Lexical Database for Computational Historical Linguistics"
- Red accent color (#990000) for headings/links

**Collections Cards:**
- Three cards (Full / Core / CORECOG)
- Each with: dataset count, form count, description, download button
- Download buttons in Uppsala red
- Grey background (#E6E6E6) for card containers

**Citation Box:**
- Bordered section with BibTeX
- Copy button for convenience

**Contact/About:**
- Tiago Tresoldi
- Uppsala University affiliation
- Email, GitHub link

### Datasets Page (datasets.html)

**Statistics Tables:**
- Comparison table (3 collections × key metrics)
- Quality metrics section
- Data coverage charts (text-based, simple)

**Collection Details:**
- Expandable sections for each collection
- Dataset lists for Core and CORECOG

## Implementation Steps

### Phase 1: Template Creation
1. Create templates/website/ directory
2. Create base.html.j2 (layout, CSS, header, footer)
3. Create index.html.j2 (landing page content)
4. Create datasets.html.j2 (dataset details)

### Phase 2: CSS Setup
1. Create docs/css/ directory
2. Download Pico CSS to docs/css/pico.min.css
3. Create docs/css/custom.css with Uppsala colors
4. Define custom styles (cards, buttons, sections)

### Phase 3: Website Generation
1. Add build_website() function to prepare_release.py
2. Extract stats from validation reports
3. Render templates to docs/
4. Test locally (open docs/index.html in browser)

### Phase 4: GitHub Pages Setup
1. Create docs/.nojekyll file
2. Commit docs/ to repository
3. Configure GitHub Pages settings
4. Test deployment

### Phase 5: Integration Testing
1. Run full release workflow
2. Verify website updates correctly
3. Check responsive design (mobile/desktop)
4. Validate all links work

## CSS Custom Styles (custom.css)

```css
:root {
    --uppsala-red: #990000;
    --uppsala-grey: #E6E6E6;
    --text-color: #000000;
    --bg-color: #FFFFFF;
}

/* Override Pico defaults with Uppsala colors */
a { color: var(--uppsala-red); }
.button-primary { background: var(--uppsala-red); }
.hero { background: var(--uppsala-grey); }
.collection-card { background: var(--uppsala-grey); border-radius: 8px; }
/* Additional custom styles as needed */
```

## Content Sections (Landing Page)

1. **Hero** - Title, subtitle, brief intro
2. **About** - What is Arca Verborum? Why use it?
3. **Collections** - Three cards with stats and download links
4. **Quick Start** - Code snippet (Python/R)
5. **Citation** - How to cite (BibTeX)
6. **Contact** - Author info, GitHub link
7. **Footer** - License, acknowledgments, last updated

## Content Sections (Datasets Page)

1. **Overview** - Collection comparison table
2. **Full Collection** - Stats, description, quality metrics
3. **Core Collection** - Stats, dataset list, selection criteria
4. **CORECOG Collection** - Stats, dataset list, use cases
5. **Data Quality** - Coverage metrics, validation details
6. **Technical Details** - CLDF format, processing pipeline

## Download Links Strategy

- Use **concept DOIs** (Option A) - always point to latest version
- Display current version number prominently
- Link to "All versions" → GitHub Releases / Zenodo versions
- Three download buttons (Full / Core / CORECOG)
- Each shows: collection name, dataset count, file size estimate

## Responsive Design

- Mobile-first approach (Pico CSS handles this)
- Stack collection cards vertically on mobile
- Readable font sizes (16px base minimum)
- Touch-friendly buttons (min 44px height)
- Test on: Desktop, Tablet, Mobile

## Testing Checklist

- [ ] All links work (GitHub, Zenodo, internal)
- [ ] Statistics are accurate and formatted correctly
- [ ] Mobile responsive (test on phone)
- [ ] BibTeX formats correctly
- [ ] Download buttons are prominent
- [ ] Page loads quickly (<1 second)
- [ ] No console errors
- [ ] Works without JavaScript
- [ ] Accessible (screen reader friendly)

## Success Criteria

1. ✅ Website deployed to GitHub Pages
2. ✅ Automatically updates with each release
3. ✅ Professional, clean design with Uppsala colors
4. ✅ All essential information present and accurate
5. ✅ Mobile-responsive
6. ✅ Fast loading (<1 second)
7. ✅ Minimal maintenance required

## Timeline

- **Phase 1** (Templates): ~2 hours
- **Phase 2** (CSS): ~1.5 hours
- **Phase 3** (Generation): ~1 hour
- **Phase 4** (GitHub Pages): ~0.5 hours
- **Phase 5** (Testing): ~1 hour
- **Total: ~6 hours**

## Decisions Made

| Aspect | Choice | Rationale |
|--------|--------|-----------|
| Generator | Pure HTML + Jinja2 | Same ecosystem, full control |
| Structure | docs/ folder in master | Simple, one repo |
| Pages | 2 pages (landing + datasets) | Clean, focused |
| Design | Research/professional | Academic credibility |
| Colors | Uppsala red/grey/white/black | User preference |
| Integration | Automated in prepare_release.py | Always in sync |
| DOIs | Concept DOI (latest) | User choice (Option A) |
| Domain | Deferred | Configure later |
| Additional pages | Minimal (contact inline) | Keep simple |
| Logo | None | User choice |
| Analytics | None | User choice |
| Version history | Link to GitHub/Zenodo | Simple |

## Next Steps

1. Create templates (base, index, datasets)
2. Set up CSS (download Pico, create custom.css)
3. Modify prepare_release.py (add build_website function)
4. Test locally
5. Deploy to GitHub Pages
6. Integrate with first release workflow
