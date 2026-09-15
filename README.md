# Woow_haos_ha_core

以**官方 Home Assistant Core 2026.9.1 映像**為基底的最小 Supervisor add-on，供與 WoowTech Podman／k3s 套件做同版本部署及備份還原測試。

> 這是 WOOWTECH 維護的第三方 Supervisor 封裝，不是 Home Assistant 官方 add-on，也不會替換 HAOS 主 Core。Core 本體不重編譯、不品牌化，不包含 multi-core 倉庫的 custom components 或配置 seed。

## 三平台基準

| 平台 | 倉庫 | HA Core版本 |
|---|---|---|
| Podman／Quadlet | [Woow_podman_homeassistant](https://github.com/WOOWTECH/Woow_podman_homeassistant) | 查證時固定2026.9.1 |
| k3s／Helm | [Woow_k3s_homeassistant](https://github.com/WOOWTECH/Woow_k3s_homeassistant) | 現有預設仍是`stable`；測試須覆寫為2026.9.1 |
| HAOS／Supervisor | 本倉庫 | 官方2026.9.1，amd64/aarch64基底digest固定 |

`version-lock.json`記錄官方index、每個platform manifest及config digest。HA Core版本是 **2026.9.1**；add-on包裝版本 **2026.9.1-1** 是另一個版本號。此倉庫不更動其他倉庫或既有部署。

**同版本是必要的控制條件，不是跨平台還原自動成功的保證。** Recorder資料庫、完整`/config`、認證資料、平台專屬integration及備份格式仍須對齊。

## 封裝邊界

- 官方基底：`ghcr.io/home-assistant/home-assistant:2026.9.1`，再以每架構digest鎖定。
- Dockerfile只加入一個環境隔離entrypoint及add-on標籤；不執行pip安裝、不更改Core程式／前端。
- entrypoint不讓Core主程序繼承`SUPERVISOR_TOKEN`、`HASSIO_TOKEN`、`HASSIO`、`SUPERVISOR`，再執行官方`/init`。這不是承諾Docker管理API看不到Supervisor注入的容器環境；管理權限本身不屬此隔離邊界。
- `hassio_api`與`homeassistant_api`關閉，無host network、Docker socket或硬體裝置授權。
- 本add-on獨立的`addon_config`掛載成`/config`，不掛載或修改HAOS主Core的配置。
- 不自動seed、搬移或修補還原資料。**官方Core本身在空配置目錄首次啟動時仍會正常建立預設資料及onboarding。**
- 預設`boot: manual`、`backup: cold`、stop timeout300秒、對外8123映射為null。

## 安裝與首次使用

1. 在Supervisor Add-on Store／Apps的Repositories加入：
   `https://github.com/WOOWTECH/Woow_haos_ha_core`
2. 安裝 **Home Assistant Core (official image)**。本repo使用Supervisor本地建置薄封裝，會下載固定官方基底；先確認空間，不能以配置檔很小推定映像很小。
3. 在Network設定指定**未被使用的宿主機埠**，例如8129；預設不開放埠，避免占用主Core的8123或既有multi-core的8124–8128。
4. 若是還原目標，**不要先按Start/onboarding**。先按測試計畫完成原生還原及啟動前內容核對。
5. 新建獨立實例時才Start並完成onboarding；UI為`http://<HAOS-host>:<selected-port>`。

這是隔離Container網路，LAN discovery／Bluetooth／Zigbee／Matter硬體直通不在初始版本範圍。不要為了測試直接開host networking或共用主Core硬體。

詳細操作見 [`ha_core/DOCS.md`](ha_core/DOCS.md)。

## 備份／還原相容性

- Supervisor備份此add-on和其自己的配置；使用cold backup，保留完整`/config`，包含隱藏`.storage`及Recorder SQLite檔案／sidecars。
- **不要把Podman `config.tgz`或Kopia repository直接當成Supervisor backup tar。** 跨格式轉換須另有受驗證的適配層；本初版不捏造備份封裝或宣稱已支援任意輸入。
- Podman預設SQLite；k3s chart預設帶PostgreSQL。若做同資料鏈，先採一致Recorder模式；SQLite→PostgreSQL不是單純複製資料檔。
- 不把較新HA建立的資料庫直接交給舊Core。還原前對齊固定Core版本，勿使用會移動的`stable`作測試基準。
- 主Core／品牌版的`.storage`可能含平台或custom integration依賴。不能保證移到官方獨立Core後所有integration均可用，也不會偷偷刪記錄來製造成功。
- 本repo不替換HAOS主Core、不要求升級主Core至2026.9.1。

## k3s測試覆寫值

`examples/k3s-values.2026.9.1.yaml`針對現有chart1.2.0固定Core版本並關閉PostgreSQL部署。該chart仍無條件引用env Secret，所以另附**刻意不含憑證**的`k3s-empty-secret.yaml`。

注意：
- 要檢查還原的`configuration.yaml`／`secrets.yaml`，確認Recorder確實使用SQLite；關閉Postgres Pod不會替你轉換Recorder設定。
- overlay沒有自動解決PVC選擇、埠衝突或容量問題，須使用新隔離namespace並明確審查StorageClass。
- chart目前Deployment replica固定1，沒有restore-mode開關。**不能直接install後再還原資料**；需要先完成還原前禁啟動的chart/流程調整。
- chart目前採tag而非image digest欄位；跨平台驗收仍要確認實際拉取的platform/config digest符合`version-lock.json`，不是只比對版本字串。

## 驗證狀態

初版提供靜態套件檢查、版本／digest一致性檢查及entrypoint環境隔離測試。

```sh
python3 -m pip install -r requirements-test.txt
python3 -m unittest discover -s tests -v
sh -n ha_core/rootfs/usr/local/bin/ha-core-entrypoint
```

**尚未完成：** 兩架構Supervisor實際建置／安裝、同版本HA Core三平台原生backup/restore與功能驗收。GitHub CI通過不等於這些真機測試通過。先前n8n的6/6結果不挪用到此套件。

## 原始碼與授權

本倉庫的封裝／測試／文件採MIT。Home Assistant Core及官方映像內其他軟體保留各自原有授權；不以本倉庫授權重新授權上游程式。

- [Home Assistant Core](https://github.com/home-assistant/core)
- [Supervisor app configuration](https://developers.home-assistant.io/docs/apps/configuration/)
- [跨平台基準決策](docs/plans/official-core-baseline.md)
