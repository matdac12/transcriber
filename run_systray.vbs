Set objShell = CreateObject("WScript.Shell")
strPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
objShell.Run "cmd /c cd """ & strPath & """ && venv\Scripts\pythonw.exe systray_dictation.py", 0, False
