# Public GitHub Pages blog instructions

This repository is a public GitHub Pages affiliate blog. Treat every file and its Git history as publicly visible.

## Safety and privacy

- Never create, request, repeat, or commit secrets: API keys, access tokens, passwords, private keys, `.env` values, GitHub Actions secrets, login URLs containing credentials, or service-account files.
- Never include the blog owner's personal information unless it is already deliberately published in the repository: real name, home address, private email address, telephone number, birth date, or account identifiers.
- Do not add analytics, advertising, affiliate-network, or third-party service credentials. If a feature requires a secret, explain what environment variable or GitHub Actions Secret the owner must configure; do not supply a value or put a placeholder that resembles a real credential.
- An affiliate link that the owner has explicitly provided, or that appears in `.github/approved-affiliate-links.md`, may be included in published article content. Use at most three links in one article, only when each entry's stated topic is directly related to the article, and copy each complete HTML code without alteration. Do not create or modify search-query, tracking, or redirect URLs; add a separately owner-provided code to the registry for a new query. Do not invent affiliate links, tracking IDs, or login details.
- Before proposing a commit, check that no secret or personal data has been added. If any is found, stop and tell the owner what must be removed or rotated.

## Article writing

- Write blog articles in natural Japanese unless the owner asks for another language.
- Keep claims accurate and distinguish fact, opinion, and personal experience. Do not fabricate product use, results, reviews, prices, statistics, sources, or testimonials.
- Include a clear affiliate disclosure when an article contains affiliate links, for example: 「当サイトはアフィリエイト広告を利用しています。」
- Do not make misleading earnings guarantees, medical/legal/financial promises, or unsupported comparisons. In particular, do not state or imply that a side business will reliably earn money.
- Do not copy text, product descriptions, reviews, tables, images, or charts from other sites. Use only original prose, short properly attributed quotations, or assets whose use is authorized.
- Do not state time-sensitive facts such as prices, discounts, stock status, rankings, specifications, campaign terms, or laws unless they have been checked against a current official source. If they cannot be checked, flag them for owner review instead of guessing.
- Use only sources that are relevant and credible. Provide the source URL for factual claims that the owner needs to verify before publication.
- Produce only static-site files suitable for GitHub Pages. Do not add server-side code or require hidden runtime configuration for an article to work.

## Public-repository hygiene

- Use generic placeholders such as `YOUR_ANALYTICS_ID` only in documentation when necessary, and state that they must not be committed with real values.
- Prefer links to official sources for factual claims that may change, and identify when information needs the owner's review before publication.
