# deploy_to_quest3.ps1
# Helper script to deploy Godot VR app to Quest 3

Write-Host "===== Quest 3 Deployment Helper =====" -ForegroundColor Cyan
Write-Host ""

# Check if ADB is available
Write-Host "Checking ADB connection..." -ForegroundColor Yellow
$adbCheck = & adb devices 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: ADB not found. Please install Android SDK Platform Tools." -ForegroundColor Red
    Write-Host "Download from: https://developer.android.com/tools/releases/platform-tools" -ForegroundColor Yellow
    exit 1
}

Write-Host $adbCheck
Write-Host ""

# Check if Quest 3 is connected
$devices = & adb devices | Select-String "device$"
if ($devices.Count -eq 0) {
    Write-Host "ERROR: No Quest 3 device found." -ForegroundColor Red
    Write-Host "Please connect Quest 3 via USB and enable USB debugging." -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Quest 3 connected" -ForegroundColor Green
Write-Host ""

# Check if APK exists
$apkPath = ".\lidar_quest3.apk"
if (-not (Test-Path $apkPath)) {
    Write-Host "ERROR: APK not found at $apkPath" -ForegroundColor Red
    Write-Host "Please export the project from Godot first:" -ForegroundColor Yellow
    Write-Host "  1. Open Godot" -ForegroundColor White
    Write-Host "  2. Go to Project → Export" -ForegroundColor White
    Write-Host "  3. Select Quest 3 preset" -ForegroundColor White
    Write-Host "  4. Click 'Export Project'" -ForegroundColor White
    Write-Host "  5. Save as 'lidar_quest3.apk' in li-dar folder" -ForegroundColor White
    exit 1
}

Write-Host "✓ Found APK: $apkPath" -ForegroundColor Green
Write-Host ""

# Get package name (typically com.godot.lidar or similar)
$packageName = "com.godotengine.lidarvr"

# Uninstall old version if exists
Write-Host "Checking for existing installation..." -ForegroundColor Yellow
$existing = & adb shell pm list packages | Select-String $packageName
if ($existing) {
    Write-Host "Uninstalling old version..." -ForegroundColor Yellow
    & adb uninstall $packageName
    Write-Host "✓ Old version uninstalled" -ForegroundColor Green
} else {
    Write-Host "No existing installation found" -ForegroundColor Gray
}
Write-Host ""

# Install new APK
Write-Host "Installing APK to Quest 3..." -ForegroundColor Yellow
& adb install -r $apkPath
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Installation successful!" -ForegroundColor Green
} else {
    Write-Host "ERROR: Installation failed" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Launch app
Write-Host "Launching app on Quest 3..." -ForegroundColor Yellow
& adb shell am start -n "$packageName/com.godot.game.GodotApp"
Write-Host "✓ App launched" -ForegroundColor Green
Write-Host ""

# Show logcat
Write-Host "===== App Logs (Ctrl+C to exit) =====" -ForegroundColor Cyan
Write-Host "Watching for UDP and point cloud messages..." -ForegroundColor Gray
Write-Host ""
& adb logcat -s "godot:D" "Godot:D" "DEBUG:D"
