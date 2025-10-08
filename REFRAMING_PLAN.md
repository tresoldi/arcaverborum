# Arca Verborum Reframing Plan

## Current Framing vs. Desired Framing

### Current Framing
Arca Verborum is presented as "analysis-ready versions of comparative wordlist data from Lexibank"
- Positioned as a derivative/preprocessing of Lexibank
- Focus on solving CLDF normalization problem
- Version letter "A" mentioned in code but not prominently explained

### Desired Framing
Arca Verborum as a **project** for lexical data in computational historical linguistics
- Multiple data source types (Series/Editions/Streams - see terminology below)
- **Series A**: Lexibank-derived data (current implementation)
- **Future Series**: Wiktionary, other sources
- Series A serves as foundation for bootstrapping other series
- Each series has same structure but different data provenance

---

## Terminology Options

What to call the letter-based divisions (A, B, C, etc.)?

### Option 1: "Series"
**Arca Verborum Series A, Series B, etc.**
- **Pros**: Common in publishing, implies progression, feels professional
- **Cons**: Could imply chronological sequence rather than parallel tracks
- **Examples**: "Series A focuses on...", "The Lexibank Series"
- **Usage**: "Download Series A.full.20251008"

### Option 2: "Edition"
**Arca Verborum Edition A, Edition B, etc.**
- **Pros**: Familiar from publishing, implies distinct versions
- **Cons**: Could suggest revisions rather than different data sources
- **Examples**: "Edition A is derived from...", "Lexibank Edition"
- **Usage**: "Download Edition A.full.20251008"

### Option 3: "Stream"
**Arca Verborum Stream A, Stream B, etc.**
- **Pros**: Implies ongoing flow of data, modern terminology
- **Cons**: Less formal, might suggest real-time updates
- **Examples**: "Stream A provides...", "The Lexibank Stream"
- **Usage**: "Download Stream A.full.20251008"

### Option 4: "Line"
**Arca Verborum Line A, Line B, etc.**
- **Pros**: Simple, implies parallel tracks, product-line feel
- **Cons**: Generic, might be confused with lineage/phylogeny
- **Examples**: "Line A contains...", "Product Line A"
- **Usage**: "Download Line A.full.20251008"

### Option 5: "Track"
**Arca Verborum Track A, Track B, etc.**
- **Pros**: Implies parallel paths, clear separation
- **Cons**: Could suggest ranking or progress
- **Examples**: "Track A is based on...", "The Lexibank Track"
- **Usage**: "Download Track A.full.20251008"

**My recommendation**: **Series** - Most professional, clear implication of related but distinct offerings, works well in academic context.

---

## Messaging Strategy

### New Tagline
**Current**: "A Global Lexical Database for Computational Historical Linguistics"
**Proposed**: Keep the same OR "A Multi-Source Lexical Database for Computational Historical Linguistics"

### New "What is Arca Verborum?" Section

**Structure:**
1. **Opening paragraph**: Position as project/initiative
2. **Data series explanation**: Introduce the multi-source concept
3. **Series A details**: Current Lexibank-based data
4. **Why Series A matters**: Explain benefits, bootstrapping role
5. **Use cases**: Keep existing list

**Proposed text:**

> Arca Verborum is a project providing analysis-ready lexical databases for computational historical linguistics. The project integrates data from multiple sources, structured for immediate use in research and education.

> **Data Series**
>
> Arca Verborum organizes data into distinct series, each derived from different sources but sharing a common structure:
>
> - **Series A (Lexibank)**: Comparative wordlists from the Lexibank initiative - 149 datasets, 2.9M forms across 9,700+ languages
> - **Future series**: Planned integration of Wiktionary data, etymological databases, and other sources
>
> **Why Series A?**
>
> While CLDF's normalized structure is excellent for data integrity, it requires significant preprocessing before analysis. Series A provides denormalized, pre-joined CSV files so you can start working immediately. This series also serves as the foundation for enriching and validating data from other sources.
>
> **Perfect for:**
> - Rapid method development and prototyping
> - Student projects and teaching computational linguistics
> - Cross-linguistic statistical analysis
> - Training machine learning models on linguistic data

---

## Files to Update

### Website (templates/website/index.html.j2)
- [ ] Update "What is Arca Verborum?" section
- [ ] Add explanation of Series concept
- [ ] Rename "Collections" section to "Series A Collections" or keep as-is?
- [ ] Update download button context text
- [ ] Add forward-looking statement about future series

### README.md
- [ ] Update opening description
- [ ] Add Series concept explanation
- [ ] Update "For Historical Linguists" section
- [ ] Consider adding roadmap section for future series

### Documentation Files
- [ ] docs/RELEASE_WORKFLOW.md: Update "Version Scheme" section
- [ ] VERSION_FORMAT_CHANGE_PLAN.md: Update terminology from "major version/data source type" to chosen term
- [ ] Consider creating new SERIES_OVERVIEW.md document

### Code Comments
- [ ] prepare_release.py: Update comment from "# Major version letter (A=Lexibank, B=Wiktionary, etc.)"
- [ ] No code logic changes needed!

### Templates
- [ ] templates/DATASET_DESCRIPTION.md.j2: Add series context if needed
- [ ] templates/RELEASE_NOTES.md.j2: Mention series in header?

---

## Questions for You

### Q1: Terminology (REQUIRED)
**Which term should we use?**
- A. **Series** (recommended)
- B. Edition
- C. Stream
- D. Line
- E. Track
- F. Other (please specify)

### Q2: Series A Naming (REQUIRED)
**How should we refer to Series A in documentation?**
- A. "Series A (Lexibank)" - Always include source name
- B. "Series A" - Use series letter primarily, mention Lexibank in description
- C. "Lexibank Series" - Source name first
- D. Other preference

### Q3: Future Series Preview (REQUIRED)
**How much detail about future series should we include?**
- A. Minimal - Just mention "future series" generically
- B. Moderate - Name Wiktionary as planned Series B
- C. Detailed - Provide roadmap with multiple planned sources
- D. None yet - Wait until Series B is closer to release

### Q4: Collections Section (OPTIONAL)
**Should we rename the "Collections" section on the website?**
- A. Keep as "Collections" (Core/Full/CoreCog are universal across series)
- B. Rename to "Series A Collections"
- C. Rename to "Available Collections"
- D. Other suggestion

### Q5: Bootstrapping Explanation (OPTIONAL)
**How much should we emphasize that Series A will bootstrap other series?**
- A. Prominent - Key part of value proposition
- B. Mention it - Include in "Why Series A?" section
- C. Minimal - Only in technical documentation
- D. Not yet - Wait until we actually use it for that purpose

### Q6: Version Display (OPTIONAL)
**Should the version be displayed differently?**
- Current: "vA.20251008" in footer
- Option A: Keep as-is
- Option B: "Series A, v20251008" or "A/20251008"
- Option C: "v20251008 (Series A)"

### Q7: Tagline (OPTIONAL)
**Should we update the main tagline?**
- A. Keep "A Global Lexical Database..." (singular)
- B. Change to "Multi-Source Lexical Database..."
- C. Other suggestion

### Q8: Naming Pattern (TECHNICAL)
**Should future series follow the same three-collection pattern?**
- Series B (Wiktionary): Will it also have Full/Core/CoreCog?
- Or will different series have different collection schemes?
- This affects how we describe the collection structure

---

## Implementation Approach

Once you answer the questions, I'll:

1. **Create updated content** for all identified files
2. **Show you previews** of key sections before implementing
3. **Update in batches**:
   - Batch 1: Website (most visible)
   - Batch 2: README and documentation
   - Batch 3: Code comments and templates
4. **Regenerate website** with new content
5. **Commit with comprehensive message**

---

## Notes

- The infrastructure already supports this! The version format was designed for this.
- No code logic changes needed - purely messaging/documentation
- This positions Arca Verborum as more ambitious and forward-looking
- Clarifies relationship with Lexibank (source, not just "preprocessing")
- Makes future expansion explicit rather than surprising users later
