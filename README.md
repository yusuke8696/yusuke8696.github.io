# yusuke8696.github.io

## 検索エンジン別サイトマップ

GitHub Pagesの標準Jekyllビルドで次の2ファイルを自動生成します。

- Google Search Console: `https://yusuke8696.github.io/sitemap_google.xml`
- Bing Webmaster Tools: `https://yusuke8696.github.io/sitemap_bing.xml`

どちらもUTF-8の標準XMLサイトマップ（urlset / url / loc、絶対URL）です。Bing版は従来と同じXML構造を使います。既存の `sitemap.xml` は変更せず残しているので、登録済みのURLも引き続き利用できます。

新しい2ファイルは `_includes/search-sitemap.xml` を共有し、トップページと `articles/` 以下のHTMLを自動収集します。記事PRが下書きの間は本番に出ず、mainへのマージとPagesビルド後に反映されます。記事ファイルをmainへ置くと掲載対象になるため、未公開の記事はブランチで管理してください。

ソースのXMLにはJekyllのfront matterとLiquidが含まれます。Search Console等にはGitHubのソースURLではなく、上記の公開URLを登録してください。PagesのSourceが「Deploy from a branch」でJekyllを使う標準構成が前提です。`.nojekyll` を追加したり、未ビルドのソースをそのまま配信する設定にすると動作しません。

PRの `Check sitemaps` は実際のPages用JekyllビルドとXML解析、記事網羅性、既存サイトマップの保持を検証します。

既存XMLもGoogleの対応形式です。URLを分けるだけでGoogleの取得エラーが解消する保証はありません。

参考: [Google公式の対応サイトマップ形式](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap?hl=ja)
