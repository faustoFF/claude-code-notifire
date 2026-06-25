#requires -Version 5.1
<#
.SYNOPSIS
    Shows a native Windows toast from a JSON payload using the WinRT API.
.DESCRIPTION
    Reads { appId, sound, soundFile, title, lines[] } from -PayloadPath and
    displays a ToastGeneric notification. When soundFile is set the toast is
    silent and the .wav is played via SoundPlayer (independent of the Windows
    sound scheme). Compatible with Windows PowerShell 5.1.
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$PayloadPath
)

$ErrorActionPreference = 'Stop'

$payload = Get-Content -LiteralPath $PayloadPath -Raw -Encoding UTF8 | ConvertFrom-Json

[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom, ContentType = WindowsRuntime] | Out-Null

$texts = @([System.Security.SecurityElement]::Escape([string]$payload.title))
foreach ($line in $payload.lines) {
    if ($line) { $texts += [System.Security.SecurityElement]::Escape([string]$line) }
}
$textXml = ($texts | ForEach-Object { "<text>$_</text>" }) -join ''

if ($payload.sound) {
    $audioXml = "<audio src='ms-winsoundevent:Notification.Default'/>"
} else {
    $audioXml = "<audio silent='true'/>"
}

$toastXml = "<toast><visual><binding template='ToastGeneric'>$textXml</binding></visual>$audioXml</toast>"

$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($toastXml)

$toast = New-Object Windows.UI.Notifications.ToastNotification $xml
if ($payload.tag) { $toast.Tag = [string]$payload.tag }
if ($payload.group) { $toast.Group = [string]$payload.group }
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier([string]$payload.appId).Show($toast)

if ($payload.soundFile) {
    (New-Object System.Media.SoundPlayer([string]$payload.soundFile)).PlaySync()
}
