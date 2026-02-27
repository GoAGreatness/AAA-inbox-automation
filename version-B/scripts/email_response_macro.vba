' ============================================================
' Email Response Generator - Outlook VBA Macro
' ============================================================
' HOW TO INSTALL:
'   1. Open Outlook
'   2. Press Alt+F11 to open the VBA editor
'   3. In the left panel, double-click "ThisOutlookSession"
'   4. Paste this entire file into the editor
'   5. Press Ctrl+S to save
'   6. Close the VBA editor
'
' HOW TO ADD BUTTONS TO TOOLBAR:
'   1. Right-click the Quick Access Toolbar (top-left of Outlook)
'   2. Click "Customize Quick Access Toolbar"
'   3. Under "Choose commands from", select "Macros"
'   4. Add "Project.ThisOutlookSession.GenerateEmailResponse"
'   5. Add "Project.ThisOutlookSession.ImportSentEmails"
'   6. Click OK
'
' HOW TO USE:
'   1. Click "Import Sent Emails" button first (first time, and periodically)
'   2. Click on any email in Outlook (reading pane or shared inbox)
'   3. Click "Generate Response" button - Chrome opens with the email pre-loaded
'   4. Generate, copy the response, paste into your Outlook reply
' ============================================================


' ------------------------------------------------------------
' Generate response for selected email - opens Chrome webapp
' ------------------------------------------------------------
Sub GenerateEmailResponse()

    Dim objItem As Object
    Dim objWin As Object
    Dim objShell As Object
    Dim strSubject As String
    Dim strSenderName As String
    Dim strSenderEmail As String
    Dim strBody As String
    Dim strURL As String

    ' Try reading pane selection
    On Error Resume Next
    If Not Application.ActiveExplorer Is Nothing Then
        If Application.ActiveExplorer.Selection.Count > 0 Then
            Set objItem = Application.ActiveExplorer.Selection.Item(1)
        End If
    End If

    ' Fallback: try open email window
    If objItem Is Nothing Then
        If Not Application.ActiveInspector Is Nothing Then
            Set objItem = Application.ActiveInspector.CurrentItem
        End If
    End If

    ' Fallback: iterate open inspectors
    If objItem Is Nothing Then
        Dim oInsp As Object
        For Each oInsp In Application.Inspectors
            Set objItem = oInsp.CurrentItem
            Exit For
        Next
    End If

    On Error Resume Next

    If objItem Is Nothing Then
        MsgBox "Please select an email first.", vbExclamation, "Email Response Generator"
        Exit Sub
    End If

    ' Extract email fields
    strSubject = objItem.Subject
    strSenderName = objItem.SenderName
    strSenderEmail = objItem.SenderEmailAddress
    strBody = objItem.Body

    ' Truncate body
    If Len(strBody) > 3000 Then
        strBody = Left(strBody, 3000)
    End If

    ' Build URL
    strURL = "https://localhost:3000/src/webapp/index.html" & _
             "?subject=" & URLEncode(strSubject) & _
             "&sender_name=" & URLEncode(strSenderName) & _
             "&sender_email=" & URLEncode(strSenderEmail) & _
             "&body=" & URLEncode(strBody)

    ' Open Chrome
    Set objShell = CreateObject("WScript.Shell")
    objShell.Run "cmd /c start chrome """ & strURL & """", 0, False

End Sub


' ------------------------------------------------------------
' Import last 50 sent emails into AI knowledge base (ChromaDB)
' Triggered manually via Quick Access Toolbar button.
' Uses MD5-based IDs on backend so duplicates are safe to send.
' Run this at least once before first use, then periodically.
' ------------------------------------------------------------
Sub ImportSentEmails()

    Dim objFolder As Object
    Dim objItems As Object
    Dim objItem As Object
    Dim objHttp As Object
    Dim emailsJson As String
    Dim jsonBody As String
    Dim count As Integer
    Dim maxEmails As Integer

    maxEmails = 50

    On Error GoTo ImportError

    ' Fetch shared mailbox name from backend config
    Dim strSharedMailbox As String
    Dim objConfigHttp As Object
    Set objConfigHttp = CreateObject("WinHttp.WinHttpRequest.5.1")
    objConfigHttp.Open "GET", "https://localhost:5000/api/user-config", False
    objConfigHttp.Option(4) = 13056
    objConfigHttp.Send
    Dim configJson As String
    configJson = objConfigHttp.ResponseText

    ' Simple parse - extract shared_mailbox_name value from JSON
    Dim nameStart As Long
    nameStart = InStr(configJson, """shared_mailbox_name"":""")
    If nameStart > 0 Then
        nameStart = nameStart + Len("""shared_mailbox_name"":""")
        Dim nameEnd As Long
        nameEnd = InStr(nameStart, configJson, """")
        strSharedMailbox = Mid(configJson, nameStart, nameEnd - nameStart)
    End If

    ' Try to find shared mailbox Sent Items if name is configured
    Dim foundShared As Boolean
    foundShared = False

    If Len(strSharedMailbox) > 0 Then
        Dim oStore As Object
        For Each oStore In Application.Session.Stores
            If InStr(LCase(oStore.DisplayName), LCase(strSharedMailbox)) > 0 Then
                Set objFolder = oStore.GetDefaultFolder(5) ' 5 = olFolderSentMail
                foundShared = True
                Exit For
            End If
        Next
    End If

    ' Fallback to personal Sent Items if shared mailbox not found
    If Not foundShared Then
        Set objFolder = Application.Session.GetDefaultFolder(5)
    End If

    Set objItems = objFolder.Items
    objItems.Sort "[SentOn]", True  ' Most recent first

    ' Build JSON array of sent emails
    emailsJson = "["
    count = 0

    Dim i As Integer
    For i = 1 To objItems.Count
        If count >= maxEmails Then Exit For

        Set objItem = objItems.Item(i)

        ' Only process mail items (Class 43 = olMail)
        If objItem.Class = 43 Then
            Dim strSubject As String
            Dim strBody As String
            strSubject = objItem.Subject
            strBody = objItem.Body

            ' Truncate body to keep payload manageable
            If Len(strBody) > 500 Then
                strBody = Left(strBody, 500)
            End If

            If count > 0 Then emailsJson = emailsJson & ","
            emailsJson = emailsJson & "{""subject"":""" & JSONEscape(strSubject) & _
                         """,""body"":""" & JSONEscape(strBody) & """}"
            count = count + 1
        End If
    Next i

    emailsJson = emailsJson & "]"
    jsonBody = "{""emails"":" & emailsJson & "}"

    ' POST to backend - sync with small payload (50 emails x 500 chars)
    Set objHttp = CreateObject("WinHttp.WinHttpRequest.5.1")
    objHttp.Open "POST", "https://localhost:5000/api/import-sent", False
    objHttp.SetRequestHeader "Content-Type", "application/json"
    objHttp.Option(4) = 13056  ' Ignore SSL errors (self-signed cert)
    objHttp.Send jsonBody

    MsgBox count & " sent emails imported into AI knowledge base.", vbInformation, "Import Complete"
    Exit Sub

ImportError:
    MsgBox "Import failed. Make sure the backend server is running on port 5000.", vbExclamation, "Import Error"
    Exit Sub

End Sub


' ------------------------------------------------------------
' URL encoding - converts text to safe URL characters
' ------------------------------------------------------------
Function URLEncode(str As String) As String
    Dim result As String
    result = str
    result = Replace(result, "%", "%25")
    result = Replace(result, " ", "%20")
    result = Replace(result, "&", "%26")
    result = Replace(result, "=", "%3D")
    result = Replace(result, "+", "%2B")
    result = Replace(result, "#", "%23")
    result = Replace(result, Chr(13), "%0D")
    result = Replace(result, Chr(10), "%0A")
    result = Replace(result, """", "%22")
    result = Replace(result, "<", "%3C")
    result = Replace(result, ">", "%3E")
    result = Replace(result, "?", "%3F")
    URLEncode = result
End Function


' ------------------------------------------------------------
' JSON string escaping - makes text safe for JSON payloads
' ------------------------------------------------------------
Function JSONEscape(str As String) As String
    Dim result As String
    result = str
    result = Replace(result, "\", "\\")
    result = Replace(result, """", "\""")
    result = Replace(result, Chr(13), "\n")
    result = Replace(result, Chr(10), "\n")
    result = Replace(result, Chr(9), "\t")
    JSONEscape = result
End Function
