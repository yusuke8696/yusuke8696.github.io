# モバイルで記事下書きPRを作る設定

確認済みのGitHub Issueに `article-approved` ラベルを付けたときだけ、記事HTMLを生成して下書きPull Requestを作成します。自動マージやGitHub Pagesの公開は行いません。

## 最初に行う設定

1. GitHubのリポジトリで `Settings` → `Actions` → `General` を開きます。
2. `Workflow permissions` で、GitHub Actionsがリポジトリの内容とPull Requestを書き込めるようにします。
3. 同じ画面で、GitHub ActionsによるPull Request作成を許可します。
4. GitHubのIssuesで、`article-approved` と `automated-article` のラベルを作成します。

## モバイルからの記事作成手順

1. GitHubモバイルアプリで `記事作成依頼` Issueを作成します。
2. タイトル、記事の要約、ChatGPTなどで作成して確認したMarkdown本文を入力します。アフィリエイトリンクを使う場合だけ、正確なリンクを入力します。
3. 内容に問題がなければ `article-approved` ラベルを付けます。
4. Actionsが下書きPRを作成します。PRを確認し、事実・リンク・広告表記・著作権・個人情報をチェックします。
5. 問題がなければ自分でmainへマージします。マージ後にGitHub Pagesが公開されます。

## 注意

- Issueの内容はPublicリポジトリでは公開されます。秘密情報や個人情報を書かないでください。
- OpenAI APIや他のAI APIは使いません。GitHub ActionsはIssueのMarkdownをHTMLに整形するだけです。
- Issueに `article-approved` ラベルを付ける前に、ChatGPTで作成した本文と根拠を確認してください。
- 生成結果は下書きです。Pull Request作成は公開や内容の正確さを保証しません。
