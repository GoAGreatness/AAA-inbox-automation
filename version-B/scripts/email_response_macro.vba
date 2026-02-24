' ============================================================
' Email Response Generator - Outlook VBA Macro
' ============================================================

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

    ' DEBUG - show URL before opening
    MsgBox "URL length: " & Len(strURL) & Chr(13) & "First 200 chars: " & Left(strURL, 200), vbInformation, "Debug URL"

    ' Open Chrome
    Set objShell = CreateObject("WScript.Shell")
    objShell.Run "cmd /c start chrome """ & strURL & """", 0, False

End Sub


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
