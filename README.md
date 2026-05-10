# Daily Wallpaper Tasks

Generate a Windows wallpaper from your Obsidian task note and set it as the desktop background.

## Layout

- `config.json`: vault and note settings
- `output/`: generated wallpaper images
- `src/`: generation and wallpaper-setting code

## Next steps

1. Edit your Obsidian daily note
2. Run the generator
3. Schedule it with Task Scheduler

## Run

```powershell
python -m src.main --set-wallpaper
```

Test only, no wallpaper change:

```powershell
python -m src.main
```

This generates:

- `output/today-main.png`
- `output/today-companion.png`

Or from PowerShell:

```powershell
.\\scripts\\run-wallpaper.ps1
```

## Obsidian note format

```md
## Priorities
- [ ] First task
- [ ] Second task

## Errands
- [ ] Buy groceries

## Later
- [ ] Research one idea

## Fun
- [ ] First task
- [ ] Second task
```

The program reads every `##` or `###` section in `Today.md` and turns each section into a card on the wallpaper.

Default source note:

```text
Today.md
```

## Schedule

Run `scripts\\install-task.ps1` to create a daily Task Scheduler job.

```powershell
.\\scripts\\install-task.ps1
```

By default it runs every day at `08:00` and launches the wallpaper refresh script in a hidden PowerShell window.

If you want a different time:

```powershell
.\\scripts\\install-task.ps1 -Time 07:30
```

## Desktop Shortcut

Run `scripts\\create-shortcut.ps1` to create a desktop shortcut named `Update Today Wallpaper.lnk`.
