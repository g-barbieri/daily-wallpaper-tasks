Set-Location -LiteralPath $PSScriptRoot\..

$python = if (Get-Command python -ErrorAction SilentlyContinue) {
  "python"
} else {
  throw "Python is not available on PATH."
}

& $python -m src.main --set-wallpaper
