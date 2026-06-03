#requires -Version 5.1
<#
.SYNOPSIS
    Removes a toast from the Action Center by tag/group via the WinRT API.
.DESCRIPTION
    Reads { tag, group, appId } from -PayloadPath and calls
    ToastNotificationManager.History.Remove. The toast must have been shown with
    the same tag/group under that appId.
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$PayloadPath
)

$ErrorActionPreference = 'Stop'

$payload = Get-Content -LiteralPath $PayloadPath -Raw -Encoding UTF8 | ConvertFrom-Json

[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null

[Windows.UI.Notifications.ToastNotificationManager]::History.Remove(
    [string]$payload.tag, [string]$payload.group, [string]$payload.appId)
