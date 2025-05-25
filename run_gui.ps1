Set-Location -Path $PSScriptRoot
& .\.venv\Scripts\Activate.ps1
python -m species_verifier.gui.app
