# import_sent.ps1
# Runs in background (launched by Outlook VBA macro).
# Reads JSON payload from temp file and POSTs to the backend.

param(
    [string]$PayloadFile
)

$apiUrl = "https://localhost:5000/api/import-sent"

function Show-ToastNotification($title, $message) {
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

    $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
    $xml.LoadXml("<toast><visual><binding template='ToastGeneric'><text>$title</text><text>$message</text></binding></visual></toast>")
    $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
    $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe")
    $notifier.Show($toast)
}

try {
    # Read payload from temp file
    $jsonBody = Get-Content -Path $PayloadFile -Raw

    # Count emails in payload for notification message
    $payload = $jsonBody | ConvertFrom-Json
    $count = $payload.emails.Count

    # Encode body as UTF-8 bytes to avoid BOM/encoding issues
    $bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($jsonBody)

    # POST to backend (no -SkipCertificateCheck - cert should be trusted in machine store)
    Invoke-RestMethod `
        -Uri $apiUrl `
        -Method POST `
        -ContentType "application/json; charset=utf-8" `
        -Body $bodyBytes | Out-Null

    Show-ToastNotification "Import Complete" "$count sent emails imported into AI knowledge base."

} catch {
    Show-ToastNotification "Import Failed" "Could not reach backend. Make sure the server is running on port 5000."
} finally {
    # Clean up temp file
    if (Test-Path $PayloadFile) {
        Remove-Item $PayloadFile -Force
    }
}
