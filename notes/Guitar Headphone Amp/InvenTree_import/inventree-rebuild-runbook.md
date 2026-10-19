# InvenTree Rebuild Runbook — Raspberry Pi 5

Restores InvenTree 1.5.0 onto a fresh Pi image from `inventree-backup.tar.gz` + `export.json`.

**Target state:** InvenTree 1.5.0 at `http://10.0.0.33`, all 66 parts, 30 categories, 123 supplier parts, 7 datasheets, both plugins, three user accounts.

---

## Before you start

Have these on the Windows machine:

| File | Contains |
|---|---|
| `inventree-backup.tar.gz` | `.env`, `Caddyfile`, `docker-compose.yml`, `inventree-data/` (incl. `media/`, `plugins.txt`) |
| `export.json` | Logical DB dump — 1.5.0 / API 530 / commit `6a6736b` |

**Do not restore `inventree-data/` wholesale.** It contains the old PostgreSQL data directory written by an arm64 Postgres. Every step below extracts *specific members* from the tarball for exactly this reason — the whole point of the logical import is to not move binary DB files.

### Optional, worth 5 minutes if the old card still boots

The plugin versions aren't pinned in `plugins.txt` (bare package names), and they aren't recoverable from the tarball — plugins install into the container, not the data volume. If you can boot the old card once more:

```bash
cd ~/inventree && docker compose up -d
docker compose exec inventree-server pip list | grep -i inventree
```

Write down the `inventree-kicad-plugin` and `inventree-ipn-generator` versions. If you can't, proceed — see *Troubleshooting* if the import fails on plugin records.

---

## 1. Base OS

Everything in this runbook assumes the **same Pi** — the DHCP reservation is keyed to eth0's MAC (`d8:3a:dd:da:8a:97`), which is burned into that board, so `10.0.0.33` carries over. A different Pi needs a new reservation before any of the URL steps make sense.

Pick the branch that matches your hardware, then rejoin at *1c*.

### 1a. NVMe (preferred)

**Pull the old SD card out of the slot first.** If it's still seated, boot order may land on the failing card and you'll spend an hour wondering why nothing works.

You can't flash NVMe from a card reader, so either boot from a known-good SD and image the drive from the running system, or — simpler, and no SD needed — put the NVMe in a USB-M.2 enclosure and flash it from Windows with Raspberry Pi Imager. Then install it in the HAT.

First boot (you may need a monitor and keyboard for this part):

```bash
sudo rpi-eeprom-update -a
sudo raspi-config     # Advanced Options → Boot Order → NVMe/USB Boot
sudo reboot
```

The EEPROM update matters — older bootloader versions don't see NVMe at all.

Confirm you're actually running from it:

```bash
lsblk
findmnt /
```

Root should be `/dev/nvme0n1p2`. If it still says `mmcblk0`, the boot order didn't take.

Leave `dtparam=pciex1_gen=3` out of `/boot/firmware/config.txt` for now. It roughly doubles throughput but isn't officially certified, and stability varies by drive and HAT. Get the stack running at Gen 2 first — it's far faster than SD either way.

### 1b. SD card (fallback)

Flash Raspberry Pi OS (64-bit) to a fresh card with Raspberry Pi Imager. Use an A2-rated card from a real brand.

Be aware you're rebuilding on the same failure mode that just cost you this evening: a Postgres workload plus Docker logs is sustained small writes, which is what kills SD cards. Plan the NVMe migration rather than treating this as done.

### 1c. Common setup

```bash
sudo apt update && sudo apt full-upgrade -y
```

Install Docker:

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

Headless server, no desktop:

```bash
sudo systemctl set-default multi-user.target
```

Log out and back in (group membership doesn't apply to the current session). Verify:

```bash
docker run --rm hello-world
docker compose version
```

**Checkpoint:** both commands succeed without `sudo`, and `findmnt /` shows the device you intended to boot from.

While you're here, confirm the storage is clean — this is the check you could never get a good answer to on the old card:

```bash
sudo dmesg -T | grep -iE 'nvme|mmc|I/O error'
```

Expect device-detection lines and nothing else. Any `I/O error`, or repeated retries or resets, means stop and sort the hardware out before putting a database on it.

---

## 2. Restore configuration

Copy both files to the Pi (from Windows PowerShell):

```powershell
scp .\inventree-backup.tar.gz .\export.json margaret@10.0.0.33:~/
```

On the Pi, verify the archive before trusting it:

```bash
cd ~
gzip -t inventree-backup.tar.gz && echo "archive OK"
```

Extract only the three config files:

```bash
tar xzf inventree-backup.tar.gz \
  inventree/.env inventree/Caddyfile inventree/docker-compose.yml
```

Inspect what you got:

```bash
cd ~/inventree
ls -la
grep -nE 'TAG|SITE_URL|ALLOWED_HOSTS|TRUSTED|EXT_VOLUME|DB_' .env
```

**Pin the version.** `stable` may have moved past 1.5.0, and a version mismatch fails the import. Edit `.env` so it reads:

```
INVENTREE_TAG=1.5.0
```

If that key isn't present, add it. Confirm the compose file honours it:

```bash
grep -n 'image:' docker-compose.yml
```

You should see `inventree/inventree:${INVENTREE_TAG:-stable}`.

**Checkpoint:** `.env` exists, `INVENTREE_TAG=1.5.0`, and `INVENTREE_SITE_URL` points at `http://10.0.0.33`.

---

## 3. Restore plugins.txt and media

Plugin *code* must be installed before the import runs, because `export.json` carries plugin data records. `plugins.txt` drives that install, so it goes in first:

```bash
cd ~
tar xzf inventree-backup.tar.gz inventree/inventree-data/plugins.txt
cat inventree/inventree-data/plugins.txt
```

Expect `inventree-kicad-plugin` and `inventree-ipn-generator`. If you captured version numbers earlier, pin them now:

```
inventree-kicad-plugin==X.Y.Z
inventree-ipn-generator==X.Y.Z
```

Now the media files — datasheets, part images, company logos. These are **not** in `export.json`; it carries only the attachment *records* pointing at these paths.

```bash
tar tzf inventree-backup.tar.gz | grep -c '^inventree/inventree-data/media/'
sudo tar xzf inventree-backup.tar.gz -C ~ inventree/inventree-data/media
ls -la ~/inventree/inventree-data/media/
```

The count should be non-zero; you're expecting `attachments/part/{2,4,5,12}/*.pdf`, `part_images/`, and `company_images/`.

**Checkpoint:** `inventree-data/` contains `plugins.txt` and `media/` — and nothing else. No `pgdb/`, no old database directory:

```bash
ls -la ~/inventree/inventree-data/
```

---

## 4. Start the database and migrate

Bring up only the backing services first:

```bash
cd ~/inventree
docker compose up -d inventree-db inventree-cache
docker compose ps
```

Give Postgres a few seconds to initialize with the credentials from `.env`, then run the update task. This installs the plugins, runs migrations, and builds static files:

```bash
docker compose run --rm inventree-server invoke update
```

This takes several minutes on a Pi and pulls the 1.5.0 image on first run. Watch for plugin install lines mentioning both packages.

Verify the version matches the export header before importing:

```bash
docker compose run --rm inventree-server invoke version
```

**Checkpoint:** reports `InvenTree 1.5.0`, `API 530`. If it says anything else, stop and fix `INVENTREE_TAG` — importing across versions fails or corrupts.

---

## 5. Import the records

The JSON must be inside the data volume, since the container only sees `/home/inventree/data`:

```bash
sudo cp ~/export.json ~/inventree/inventree-data/export.json
```

Import, clearing the freshly-migrated tables first:

```bash
cd ~/inventree
docker compose run --rm inventree-server invoke import-records \
  -c -f /home/inventree/data/export.json
```

The `-c` flag clears existing data before importing — required, because `invoke update` already created rows (the admin user, default templates) that would collide.

**Checkpoint:** completes without traceback. If it fails, see *Troubleshooting*.

---

## 6. Bring everything up

```bash
docker compose up -d
docker compose ps
```

All five containers (`inventree-db`, `inventree-cache`, `inventree-server`, `inventree-worker`, `inventree-proxy`) should show `running`.

From Windows:

```powershell
curl.exe -sS -o NUL -w "%{http_code} %{size_download}`n" http://10.0.0.33/
```

A 200 with a **non-zero** byte count means the proxy is routing correctly. A 200 with `0` bytes means Caddy has no site block matching the request host — recheck `INVENTREE_SITE_URL` in `.env`, then `docker compose down && docker compose up -d`.

---

## 7. Verify

Log in as `daniel` (password carried over in the export — the `auth.user` hashes came with it).

Check in the UI:

- [ ] 66 parts, 30 categories
- [ ] Part 2 (BQ24074RGTR) → Attachments tab → `bq24074.pdf` opens
- [ ] Part 13 → datasheet link resolves (that one is a URL attachment, not a file)
- [ ] Settings → Plugins → both KiCad and IPN Generator listed, KiCad active
- [ ] `guitar_headphone_amp` BOM shows 4 lines (J1, U1, D1, R1/R2/R4)

---

## 8. Post-import fixes

### 8a. Confirm the base URL

Setting `INVENTREE_BASE_URL` lives in the *database*, not `.env`, and the export has it as `http://10.0.0.33`. If the Pi ended up on a different address, change it in Settings → Server → Site URL. A stale value here breaks `fully_qualified_url()`, which is what generates datasheet links for the KiCad plugin.

### 8b. Add the six missing KiCad categories

These categories have parts but no entry in the plugin's category list, so nine parts never reach KiCad at all. In Settings → Plugins → KiCad Library Plugin → category selection, add:

| Category | Affected parts |
|---|---|
| MOSFETs (26) | BSS138 |
| Logic (27) | CD74HC4060, 74HC14, SN74HC02 |
| Switching Diodes (28) | 1N4148W |
| LEDs (29) | Amber 0402 |
| Audio Connectors (30) | Both 3.5 mm jacks |
| Inductors (21) | 3.3 µH — sits in the parent, not in 22/23 |

### 8c. Remove the stray Datasheet parameter

Parameter template "Datasheet" (pk 2) is used once, on part 4 (USB4085), and duplicates that part's proper `datasheet` attachment. Delete the parameter from part 4, then delete the template.

### 8d. Point KiCad at the server

On the Windows machine, edit `.kicad_httplib`:

- `root_url` → `http://10.0.0.33/...`
- `timeout_categories_seconds` → something small (5–30) while you populate; raise it later

Then **fully restart KiCad** — the HTTP connection object and its category list are built once per session and have no invalidation path.

### 8e. Set up backups properly

```bash
docker compose run --rm inventree-server invoke backup
```

Writes to `/home/inventree/data/backup`. Schedule it and sync the output somewhere off the Pi.

---

## Troubleshooting

**Import fails on plugin records** — plugin version mismatch. Pin exact versions in `plugins.txt`, re-run `invoke update`, then re-run the import with `-c`.

**Import fails with encoding errors** — the target DB encoding doesn't match the dump. Recreate the database container with a UTF-8 locale.

**Postgres won't start** — an old data directory is present. `inventree-data/` should contain only `plugins.txt` and `media/` before step 4.

**Datasheets 404 after login** — media wasn't restored, or `INVENTREE_BASE_URL` is stale. Check step 3 and step 8a.

**Empty 200 from the proxy** — covered in step 6.

**Pi boots to the old SD card instead of NVMe** — card still in the slot, or boot order not set. See step 1a.

**NVMe not detected at all** — bootloader EEPROM too old. `sudo rpi-eeprom-update -a`, reboot, retry.

---

## Notes

- `export.json` contains password hashes and three real email addresses. Don't commit it or leave it in a shared folder.
- The old card threw `mmc0: Card stuck being busy!` and a hard read error at sector 13090690 — do not reuse it.
- If you ended up on SD rather than NVMe, expect the same wear failure eventually. Move the Postgres volume and Docker's data root to external storage, or plan the migration.
- Longer term, a hostname-based `INVENTREE_SITE_URL` with a static DNS entry beats a literal IP — it keeps the address in one place instead of four (Caddy, Django, the KiCad `root_url`, and every generated datasheet URL). Needs DNS resolving from the Windows box first, then change the setting. Not required for this rebuild.
