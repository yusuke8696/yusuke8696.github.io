# yusuke8696.github.io

## 検索エンジン別サイトマップ

GitHub Pagesの標準Jekyllビルドで次の2ファイルを自動生成します。

- Google Search Console: `https://yusuke8696.github.io/sitemap_google.xml`
- Bing Webmaster Tools: `https://yusuke8696.github.io/sitemap_bing.xml`

どちらもUTF-8の標準XMLサイトマップです。Google版は `url` 内に `loc` と `lastmod` をそれぞれ改行して記載します。Bing版は従来と同じXML構造を使います。既存の `sitemap.xml` は変更せず残します。

Google版は `_includes/google-sitemap.xml`、Bing版は `_includes/search-sitemap.xml` を使用し、トップページと `articles/` 以下のHTMLを自動収集します。記事PRが下書きの間は本番に出ず、mainへのマージとPagesビルド後に反映されます。

Google版の更新日は `_data/sitemap_dates.json` で管理します。HTMLを追加・変更してコミットした後、`python .github/scripts/update-sitemap-dates.py` を実行し、更新されたJSONも同じPRへコミットしてください。Gitの最終変更コミット日を使い、ビルド日で一律更新しません。内容変更を伴わない整形等のコミットでは、必要に応じて実際の内容更新日に修正してください。新記事の日付が欠ける場合はCIが失敗するため、マージ前に補完します。

ソースのXMLにはJekyllのfront matterとLiquidが含まれます。Search Console等にはGitHubのソースURLではなく、上記の公開URLを登録してください。PagesのSourceが「Deploy from a branch」でJekyllを使う標準構成が前提です。`.nojekyll` を追加したり、未ビルドのソースをそのまま配信する設定にすると動作しません。

PRの `Check sitemaps` は実際のPages用JekyllビルドとXML解析、記事網羅性、既存サイトマップの保持を検証します。

既存XMLもGoogleの対応形式です。URLを分けるだけでGoogleの取得エラーが解消する保証はありません。

参考: [Google公式の対応サイトマップ形式](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap?hl=ja)
