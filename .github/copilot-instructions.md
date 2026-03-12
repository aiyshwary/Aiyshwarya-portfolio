# Copilot Instructions for Portfolio Codebase

## Overview
This is a static portfolio site that auto-generates project cards from PDFs and JSON data. The main workflow is simple, but there are a few project-specific conventions and data flows to follow for productive AI coding.

## Key Components & Data Flow
- **index.html, styles.css, script.js**: Main UI, styling, and logic for the portfolio. The UI is responsive and single-page.
- **projects.json**: Central data file. Each entry includes `impact`, `bullets`, `techs`, and `thumbnail` fields. This file powers the project cards on the homepage.
- **assets/projects/**: Contains project PDFs, copied from `Project_Explanation_Detailed copy/`.
- **assets/images/**: Contains SVG thumbnails, one per project.
- **assets/resume.pdf**: Resume file, referenced in the UI.

## Developer Workflow
- **Local Dev Server**: Run `python -m http.server 5500` and open [http://localhost:5500](http://localhost:5500).
- **Edit Project Data**: Update `projects.json` for project card content. Add or edit `impact`, `bullets`, `techs`, and `thumbnail` fields.
- **Skills/Experience**: Update these in `script.js` (top-right panel logic).
- **Profile Photo**: Place a photo in `assets/` and reference as `avatar.jpg` in `index.html`.

## Project-Specific Patterns
- **PDF → JSON**: Project summaries are extracted from PDFs in `Project_Explanation_Detailed copy/` and enhanced into `projects.json`. Use or update `generate_pdfs.py` for automation.
- **Thumbnails**: SVGs in `assets/images/` are auto-generated. Reference them in `projects.json` via the `thumbnail` field.
- **Resume**: Keep `assets/resume.pdf` up to date; referenced in the UI.

## Conventions
- All project data is centralized in `projects.json`.
- Thumbnails and PDFs must be present in their respective folders and referenced by filename in `projects.json`.
- No build step: this is a static site, so changes are reflected immediately on refresh.

## Example: Adding a New Project
1. Place the project PDF in `assets/projects/`.
2. Generate or create a thumbnail SVG in `assets/images/`.
3. Add a new entry to `projects.json` with all required fields.
4. Refresh the site to see the new project card.

## References
- See `README.md` for setup and workflow.
- See `generate_pdfs.py` for PDF-to-JSON automation logic.
- See `script.js` for UI logic and data loading.

---

For any automation, always update `projects.json` and asset folders to keep the UI in sync with data and files.