# Windows services

Runs ASR Studio without an IDE: two Windows services that start with Windows and restart on failure.

| Service | Runs | URL |
|---|---|---|
| `ASRStudioBackend` | `python backend\server.py` (auto-reload off) | `http://localhost:<SERVER_PORT>` from `backend\.env` |
| `ASRStudioFrontend` | `next start` on a production build | `http://localhost:3000` |

The frontend depends on the backend, and the backend depends on the `MongoDB` service when it exists.

## Install

1. Create `backend\.env` and `frontend\.env.local` (see the `.env.example` files).
2. Stop any dev servers using the same ports (the script refuses to install if a port is busy).
3. Open **PowerShell as Administrator** and run:

```powershell
powershell -ExecutionPolicy Bypass -File D:\asr\services\install-services.ps1
```

The script installs [NSSM](https://nssm.cc) with winget (copied to `services\bin`), builds the frontend, then installs and starts both services. Run it again after changing code or `.env` files to rebuild and reinstall.

Options: `-FrontendPort 3000`, `-FrontendHost 127.0.0.1`, `-SkipBuild`, `-BackendServiceName`, `-FrontendServiceName`.

## Manage

```powershell
Get-Service ASRStudio*
Restart-Service ASRStudioBackend      # after backend code or backend\.env changes
Stop-Service ASRStudioFrontend, ASRStudioBackend
```

Or use `services.msc`. Logs: `services\logs\backend.log` and `services\logs\frontend.log` (rotated at 10 MB).

Frontend code or `NEXT_PUBLIC_*` changes need a rebuild: run `install-services.ps1` again.

## Uninstall

```powershell
powershell -ExecutionPolicy Bypass -File D:\asr\services\uninstall-services.ps1
```

## Notes

The services run as LocalSystem, so the install script passes in what that account cannot see in your user profile: ffmpeg/ffprobe paths, your user Python packages (`PYTHONPATH`), and the Whisper model cache (`XDG_CACHE_HOME`). If you move ffmpeg or Python, run the install script again.
