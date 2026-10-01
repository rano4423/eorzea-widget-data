# Eorzea Weather 図鑑データ

[Eorzea Weather](https://github.com/rano4423) のギャザクラ図鑑が、起動時にここから最新の `almanac.json` を取得します（設定でオフにできます）。

- `almanac.json`：ヌシ・オオヌシと未知・伝説・刻限の採集場所、検索用の読み。
- 毎週 GitHub Actions（`.github/workflows/update.yml`）で元データから作り直し、内容が変わったときだけ更新します。手動で動かすときは Actions タブの「update-almanac」→「Run workflow」。
- 元データとライセンス：`THIRD-PARTY-almanac.txt`（FF14 Fish Tracker・FFXIV Teamcraft は MIT、SudachiDict は Apache-2.0、Unihan は Unicode License v3）。
