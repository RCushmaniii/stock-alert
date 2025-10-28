# Code Signing Guide for StockAlert

## 🛡️ The Problem

Windows Defender and SmartScreen flag unsigned executables as potentially dangerous. Users see warnings like:
- "Windows protected your PC"
- "Unknown publisher"
- "This app might harm your device"

This is **normal** for new, unsigned applications but can prevent users from installing.

## ✅ The Solution: Code Signing

A **code signing certificate** digitally signs your executables, proving:
- ✅ The publisher's identity is verified
- ✅ The code hasn't been tampered with
- ✅ The software is from a trusted source

## 💰 Code Signing Certificate Providers

### Recommended Options

| Provider | Cost/Year | Reputation | Validation Time |
|----------|-----------|------------|-----------------|
| **DigiCert** | $400-500 | ⭐⭐⭐⭐⭐ Best | 1-3 days |
| **Sectigo (Comodo)** | $200-300 | ⭐⭐⭐⭐ Good | 1-3 days |
| **SSL.com** | $100-200 | ⭐⭐⭐ Budget | 1-2 days |
| **GlobalSign** | $300-400 | ⭐⭐⭐⭐ Good | 1-3 days |

### What You Need to Purchase

**For Individual Developers:**
- Standard Code Signing Certificate
- Requires: Government-issued ID, phone verification

**For Companies:**
- Organization Validated (OV) Code Signing Certificate
- Requires: Business registration documents, D&B number

### Recommended: SSL.com (Best Value)

**Product:** eSigner Code Signing Certificate  
**Cost:** ~$100/year  
**Link:** https://www.ssl.com/certificates/code-signing/

**Why SSL.com:**
- ✅ Affordable for indie developers
- ✅ Cloud-based signing (no USB token required)
- ✅ Trusted by Windows
- ✅ Fast validation (1-2 days)

## 🔧 How to Sign Your Executables

### Step 1: Install SignTool

SignTool comes with Windows SDK:

1. Download Windows SDK: https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/
2. Install only "Windows SDK Signing Tools for Desktop Apps"
3. SignTool location: `C:\Program Files (x86)\Windows Kits\10\bin\<version>\x64\signtool.exe`

### Step 2: Get Your Certificate

After purchasing from SSL.com (or other provider):

1. Complete identity verification
2. Download certificate as `.pfx` file
3. Note the password provided

### Step 3: Sign the MSI Installer

```powershell
# Set variables
$certPath = "path\to\your\certificate.pfx"
$certPassword = "your-certificate-password"
$msiPath = "dist\StockAlert-2.1.0-win64.msi"
$timestampUrl = "http://timestamp.digicert.com"

# Sign the MSI
& "C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe" sign `
    /f $certPath `
    /p $certPassword `
    /t $timestampUrl `
    /d "StockAlert - Stock Price Monitor" `
    /du "https://github.com/yourusername/stockalert" `
    $msiPath
```

### Step 4: Sign Individual Executables (Optional but Recommended)

```powershell
# Extract files from MSI first, then sign each EXE
$exeFiles = @(
    "build\exe.win-amd64-3.12\StockAlert.exe",
    "build\exe.win-amd64-3.12\StockAlertConfig.exe",
    "build\exe.win-amd64-3.12\StockAlertConsole.exe"
)

foreach ($exe in $exeFiles) {
    & "C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe" sign `
        /f $certPath `
        /p $certPassword `
        /t $timestampUrl `
        /d "StockAlert" `
        $exe
}

# Then rebuild MSI with signed executables
```

### Step 5: Verify Signature

```powershell
# Verify the signature
signtool verify /pa "dist\StockAlert-2.1.0-win64.msi"

# Should output: "Successfully verified"
```

## 🤖 Automated Signing Script

Create `sign_release.ps1`:

```powershell
# Sign StockAlert Release
# Usage: .\sign_release.ps1

param(
    [Parameter(Mandatory=$true)]
    [string]$CertPath,
    
    [Parameter(Mandatory=$true)]
    [string]$CertPassword
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "StockAlert Code Signing" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Find SignTool
$signTool = "C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe"
if (-not (Test-Path $signTool)) {
    Write-Host "❌ SignTool not found. Install Windows SDK." -ForegroundColor Red
    exit 1
}

# Timestamp server
$timestampUrl = "http://timestamp.digicert.com"

# Sign executables before building MSI
Write-Host "📝 Signing executables..." -ForegroundColor Cyan
$exeFiles = Get-ChildItem "build\exe.win-amd64-3.12\*.exe"
foreach ($exe in $exeFiles) {
    Write-Host "  Signing $($exe.Name)..." -ForegroundColor Gray
    & $signTool sign /f $CertPath /p $CertPassword /t $timestampUrl /d "StockAlert" $exe.FullName
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to sign $($exe.Name)" -ForegroundColor Red
        exit 1
    }
}

# Sign MSI
Write-Host "📦 Signing MSI installer..." -ForegroundColor Cyan
$msi = Get-ChildItem "dist\*.msi" | Select-Object -First 1
if ($msi) {
    & $signTool sign /f $CertPath /p $CertPassword /t $timestampUrl /d "StockAlert - Stock Price Monitor" $msi.FullName
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to sign MSI" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Successfully signed: $($msi.Name)" -ForegroundColor Green
} else {
    Write-Host "❌ No MSI found in dist\" -ForegroundColor Red
    exit 1
}

# Verify signatures
Write-Host ""
Write-Host "🔍 Verifying signatures..." -ForegroundColor Cyan
& $signTool verify /pa $msi.FullName
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Signature verified successfully!" -ForegroundColor Green
} else {
    Write-Host "⚠️ Signature verification failed" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Code Signing Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
```

## 🆓 Free Alternatives (Not Recommended)

### Self-Signed Certificate (Not Trusted by Windows)

```powershell
# Create self-signed cert (for testing only)
$cert = New-SelfSignedCertificate `
    -Type CodeSigningCert `
    -Subject "CN=StockAlert" `
    -CertStoreLocation "Cert:\CurrentUser\My"

# Export to PFX
$password = ConvertTo-SecureString -String "password" -Force -AsPlainText
Export-PfxCertificate -Cert $cert -FilePath "selfsigned.pfx" -Password $password

# Sign with self-signed cert
signtool sign /f selfsigned.pfx /p password /t http://timestamp.digicert.com StockAlert.exe
```

**Problem:** Users still see warnings because the certificate isn't from a trusted CA.

## 📊 Cost-Benefit Analysis

### Without Code Signing
- ❌ Windows Defender warnings
- ❌ SmartScreen blocks
- ❌ Users may not install
- ❌ Looks unprofessional
- ✅ Free

### With Code Signing ($100-400/year)
- ✅ No Windows warnings
- ✅ Professional appearance
- ✅ User trust
- ✅ Higher install rate
- ✅ Verified publisher identity
- ❌ Annual cost

**ROI:** If you have 10+ users, code signing pays for itself in trust and reduced support.

## 🎯 Recommended Workflow

### For Development/Testing
1. Build unsigned MSI
2. Test locally (allow warnings)
3. Share with beta testers (with warning instructions)

### For Public Release
1. Purchase code signing certificate (SSL.com recommended)
2. Build MSI
3. Sign all executables
4. Sign MSI installer
5. Verify signatures
6. Distribute signed MSI

### Annual Renewal
- Renew certificate before expiration
- Re-sign all releases with new certificate
- Timestamp ensures old signatures remain valid

## 📝 Alternative: Submit to Microsoft

**Free option:** Submit your MSI to Microsoft for analysis

1. Go to: https://www.microsoft.com/en-us/wdsi/filesubmission
2. Upload MSI
3. Microsoft analyzes (24-48 hours)
4. If clean, they may whitelist it

**Success rate:** ~50% (not guaranteed)

## 🔮 Future: EV Code Signing

**Extended Validation (EV) Code Signing:**
- Cost: $300-500/year
- Requires USB hardware token
- **Immediate SmartScreen reputation** (no waiting period)
- Best for commercial software

**When to upgrade:**
- When you have paying customers
- When support costs from warnings are high
- When professional image is critical

## 📚 Additional Resources

- **Microsoft Code Signing:** https://docs.microsoft.com/en-us/windows/win32/seccrypto/cryptography-tools
- **SSL.com Guide:** https://www.ssl.com/how-to/code-signing-for-windows/
- **DigiCert Guide:** https://docs.digicert.com/en/software-trust-manager/sign-with-digicert-signing-tools.html

---

**Bottom Line:** For a professional release, invest $100-200/year in code signing. For hobby/testing, document the warning bypass process clearly.
