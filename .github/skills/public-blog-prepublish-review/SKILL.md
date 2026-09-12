---
name: public-blog-prepublish-review
description: Review a public GitHub Pages affiliate-blog article or change set before publication for secrets, privacy, advertising transparency, factual support, and copyright risks.
---

# Public Blog Pre-publish Review

Use this skill when the owner asks whether an article or site change is ready to publish.

Review only. Do not silently rewrite, commit, deploy, or remove files unless the owner asks for that action.

## Review checklist

- Search the proposed content and related configuration for API keys, passwords, tokens, private URLs, `.env` values, personal contact details, or credentials embedded in links. Treat a suspected secret as a blocking issue.
- Check that affiliate content has a clear disclosure that is easy for a reader to notice. Check that promotional claims and links do not look like independent editorial content.
- Flag invented or unsupported reviews, testimonials, rankings, price claims, discounts, earnings claims, health claims, legal advice, financial advice, or time-sensitive facts without an official source.
- Flag copied-looking text and third-party images, tables, charts, or trademarks that do not have a clear permitted use or attribution.
- Check each link for an obvious mismatch between its anchor text and destination. Never follow or expose credentials in a URL.
- Check that the content does not promise earnings or results, conceal limitations, or use misleading urgency.

## Report format

Report findings in Japanese, grouped by severity:

1. `公開停止` — secrets, personal data, clear copyright concern, or clearly misleading advertising.
2. `公開前に修正` — missing disclosure, unverified material claim, broken or mismatched link, or missing source.
3. `改善提案` — clarity and reader-trust improvements.

For every finding, identify the location, explain the risk briefly, and propose a safe replacement. If no blocking issues are found, state that the review found no blocking issues, not that publication is legally guaranteed.
