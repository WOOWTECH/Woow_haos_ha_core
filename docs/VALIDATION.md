# Validation record — initial package

Observed 2026-09-15.

## Completed

- Official2026.9.1 registry index, linux/amd64 and linux/arm64 manifests and configs fetched; each content digest checked. Both configs identify Core2026.9.1, entrypoint/init and noCMD.
- Nine local unittest cases passed: repository identity, version separation, architecture pins, restore-friendly defaults, own/config mapping, host-access restrictions, absence of seed/bundledCore, real shell environment filtering/argument forwarding and k3s overlay consistency.
- Entry point passed`sh -n`.
- The actual installed Supervisor`SCHEMA_APP_CONFIG` accepted config.yaml: slugwoow_ha_core, version2026.9.1-1, bootmanual, backupcold. Validation had no install/start/restore side effect.
- Supervisor warned that`addon_config`is a legacy spelling and recommends`app_config`. The compatible spelling is deliberately retained; schema acceptance is not a promise of indefinite compatibility.

## Not yet completed

- Docker image build and output-layer comparison.
- Native Supervisor installation/start/backup/restore on either architecture.
- HA Core same-version three-platform data/application cycle.
- Recorder migration, hardware discovery/passthrough, performance or disaster-recovery certification.

A passing local test or CI run must not be reported as native migration success. Existing n8n campaign results are unrelated evidence.
