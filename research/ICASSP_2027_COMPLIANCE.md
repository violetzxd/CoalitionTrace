# ICASSP 2027 submission compliance

Verified against the official conference pages on 2026-09-20:

- The live conference Important Dates page states a regular-paper deadline of
  **2026-09-23**. The separate CMS paper-kit page still displays 2026-09-16,
  apparently predating the live-site extension. Confirm that the CMS remains open
  before final upload; do not rely on the stale kit date alone.
  <https://2027.ieeeicassp.org/important-dates/>
- Maximum four pages of technical content; the optional fifth page may contain
  only references, funding acknowledgments, and a Compliance with Ethical
  Standards statement. <https://cmsworkshops.com/ICASSP2027/papers/paper_kit.php>
- The manuscript must discuss relation to prior work.
  <https://2027.ieeeicassp.org/paper-submission-instructions/>
- IEEE requires disclosure of AI-generated article content in acknowledgments,
  identifying the system, affected sections and level of use. Editing/grammar
  assistance is treated separately but disclosure is recommended.
  <https://2027.ieeeicassp.org/author-guidelines/>
- Accepted papers require in-person presentation and author registration.
  <https://2027.ieeeicassp.org/paper-submission-instructions/>

## Artifact gates before a submission PDF is declared ready

- [ ] Four technical pages plus restricted page 5; no result or figure is placed
  on page 5.
- [ ] Authors, affiliations, ORCIDs and acknowledgments supplied by the authors.
- [ ] Every author has a valid ORCID; author names/order exactly match the CMS.
- [ ] AI-use disclosure names Codex and precisely describes code/manuscript use.
- [ ] Compliance with Ethical Standards statement and funding acknowledgments.
- [ ] All main-table values regenerate from immutable JSONL files and hashes.
- [ ] No placeholder citations, numbers, author fields or unverified claims.
- [ ] PDF font embedding, margins, page count and visual rendering checked.
- [ ] Independent reviewer signs off on theory, statistics and claim scope.

The author-identity and funding fields cannot be inferred by the research agent;
they remain an explicit human-supplied finalization dependency.
