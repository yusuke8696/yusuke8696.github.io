import { mkdir, readFile, writeFile } from "node:fs/promises";

const required = ["ARTICLE_ISSUE_NUMBER", "ARTICLE_ISSUE_TITLE", "ARTICLE_ISSUE_BODY"];
for (const name of required) if (!process.env[name]) throw new Error(`${name} is required.`);

const escapeHtml = (value) => String(value)
  .replace(/&/g, "&amp;")
  .replace(/</g, "&lt;")
  .replace(/>/g, "&gt;")
  .replace(/"/g, "&quot;");

const issueBody = process.env.ARTICLE_ISSUE_BODY.replace(/\r/g, "");
const field = (name) => {
  const expression = new RegExp(`^### ${name}\\n\\n([\\s\\S]*?)(?=^### |$)`, "m");
  return issueBody.match(expression)?.[1].trim() || "";
};

const summary = field("記事の要約");
const markdown = field("記事本文（Markdown）");
if (!summary || !markdown) throw new Error("Issueに記事の要約またはMarkdown本文がありません。");

const inline = (text) => escapeHtml(text)
  .replace(/`([^`]+)`/g, "<code>$1</code>")
  .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
  .replace(/\[([^\]]+)\]\((https:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

const renderMarkdown = (source) => {
  const lines = source.split("\n");
  const output = [];
  let list = [];
  const flushList = () => {
    if (list.length) output.push(`<ul>${list.map((item) => `<li>${inline(item)}</li>`).join("")}</ul>`);
    list = [];
  };
  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) { flushList(); continue; }
    const item = line.match(/^-\s+(.+)$/);
    if (item) { list.push(item[1]); continue; }
    flushList();
    const heading = line.match(/^(#{2,3})\s+(.+)$/);
    if (heading) output.push(`<h${heading[1].length}>${inline(heading[2])}</h${heading[1].length}>`);
    else output.push(`<p>${inline(line)}</p>`);
  }
  flushList();
  return output.join("\n\t\t\t");
};

const issueNumber = process.env.ARTICLE_ISSUE_NUMBER;
const title = process.env.ARTICLE_ISSUE_TITLE.replace(/^記事案:\s*/, "").trim();
if (!title) throw new Error("Issueのタイトルがありません。");
if (/(?:sk-|ghp_|github_pat_)[A-Za-z0-9_-]{12,}/i.test(markdown)) throw new Error("記事本文に秘密情報らしき文字列があります。");

const articlePath = `articles/article-issue-${issueNumber}.html`;
const html = `<!DOCTYPE html>
<html lang="ja">
<head>
\t<meta charset="UTF-8">
\t<meta name="viewport" content="width=device-width, initial-scale=1.0">
\t<title>${escapeHtml(title)} | AI・PC活用ブログ</title>
\t<meta name="description" content="${escapeHtml(summary)}">
\t<style>
\t\tbody { margin:0; color:#202a35; background:#f3f6f5; font-family:"Noto Sans JP","Yu Gothic",sans-serif; line-height:1.85; }
\t\theader, footer { padding:22px 20px; color:#fff; background:#07534e; }
\t\t.header-inner, main, footer > div { width:min(920px,100%); margin:0 auto; }
\t\theader a { color:#d8f4ed; text-decoration:none; }
\t\tmain { padding:54px 20px 70px; }
\t\t.article-header, article { padding:38px 42px; background:#fff; border:1px solid #dbe3e8; border-radius:10px; }
\t\tarticle { margin-top:24px; }
\t\th1, h2, h3 { line-height:1.4; } h1 { margin:0; font-size:clamp(28px,5vw,42px); } h2 { margin-top:42px; }
\t\t.lead { color:#50606b; font-size:17px; } code { padding:2px 5px; color:#07534e; background:#edf4f2; border-radius:3px; } a { color:#0b756c; }
\t\t@media (max-width:640px) { main { padding:28px 14px 48px; } .article-header, article { padding:26px 20px; } }
\t</style>
</head>
<body>
\t<header><div class="header-inner"><a href="../index.html">← AI・PC活用ブログに戻る</a></div></header>
\t<main>
\t\t<div class="article-header"><h1>${escapeHtml(title)}</h1><p class="lead">${escapeHtml(summary)}</p></div>
\t\t<article>
\t\t\t${renderMarkdown(markdown)}
\t\t</article>
\t</main>
\t<footer><div>© 2026 AI・PC活用ブログ</div></footer>
</body>
</html>
`;

await mkdir("articles", { recursive: true });
await writeFile(articlePath, html, "utf8");
const index = await readFile("index.html", "utf8");
const marker = '<div class="articles">';
if (!index.includes(marker)) throw new Error("Could not find the article list in index.html.");
const card = `            <article class="article">
                <span class="category">AI・PC活用</span>
                <h3><a href="${articlePath}">${escapeHtml(title)}</a></h3>
                <p>${escapeHtml(summary)}</p>
            </article>

`;
await writeFile("index.html", index.replace(marker, `${marker}\n\n${card}`), "utf8");
console.log(`Generated ${articlePath} from issue #${issueNumber}.`);
