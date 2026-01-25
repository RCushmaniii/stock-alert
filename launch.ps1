# StockAlert Launcher - bypasses Git's OpenSSL conflict
$env:PATH = "C:\LangAppFiles\anaconda3\Library\bin;C:\LangAppFiles\anaconda3;$env:SYSTEMROOT\system32;$env:SYSTEMROOT"
Set-Location $PSScriptRoot
Start-Process -FilePath ".\venv\Scripts\pythonw.exe" -ArgumentList "-m", "stockalert" -WindowStyle Hidden
