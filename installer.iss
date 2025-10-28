; Inno Setup Script for Whisper Dictation & File Transcriber
; This script creates a Windows installer for the application
;
; Requirements:
; 1. Install Inno Setup from: https://jrsoftware.org/isinfo.php
; 2. Run build_installer.py first to create the executables
; 3. Right-click this file and select "Compile" to build the installer

#define MyAppName "Whisper Dictation & File Transcriber"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Your Name"
#define MyAppURL "https://github.com/yourusername/dictation-app"
#define MyAppExeName "WhisperDictation.exe"
#define MyAppTranscriberName "FileTranscriber.exe"

[Setup]
; Basic app information
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\WhisperDictation
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=
InfoBeforeFile=
InfoAfterFile=
OutputDir=installer_output
OutputBaseFilename=WhisperDictation_Setup
SetupIconFile=
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

; Uninstaller
UninstallDisplayIcon={app}\{#MyAppExeName}

; Directory and group settings
DisableProgramGroupPage=yes
DisableReadyPage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode
Name: "startup"; Description: "Start Whisper Dictation automatically when Windows starts"; GroupDescription: "Auto-start:"; Flags: unchecked

[Files]
; Main executables
Source: "dist\DictationApp\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\DictationApp\{#MyAppTranscriberName}"; DestDir: "{app}"; Flags: ignoreversion

; Support files
Source: "dist\DictationApp\run_systray.vbs"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\DictationApp\Start_Dictation.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\DictationApp\README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "dist\DictationApp\QUICKSTART.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu shortcuts
Name: "{group}\Whisper Dictation (Systray)"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\File Transcriber"; Filename: "{app}\{#MyAppTranscriberName}"
Name: "{group}\Quick Start Guide"; Filename: "{app}\QUICKSTART.txt"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Desktop shortcut (optional)
Name: "{autodesktop}\Whisper Dictation"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; Quick Launch shortcut (optional, for older Windows)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\Whisper Dictation"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

; Startup shortcut (optional)
Name: "{userstartup}\Whisper Dictation"; Filename: "{app}\{#MyAppExeName}"; Tasks: startup

[Run]
; Option to launch the app after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,Whisper Dictation}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
  PythonInstalled: Boolean;
begin
  Result := True;

  // Show welcome message
  MsgBox('Welcome to Whisper Dictation & File Transcriber Setup!'#13#10#13#10 +
         'This application uses AI-powered speech recognition to:'#13#10 +
         '• Convert speech to text in real-time'#13#10 +
         '• Transcribe audio files to text'#13#10#13#10 +
         'First run will download AI models (~150MB).'#13#10 +
         'Internet connection required for first use.',
         mbInformation, MB_OK);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Additional post-install tasks can go here
  end;
end;

function InitializeUninstall(): Boolean;
var
  Response: Integer;
begin
  Response := MsgBox('Do you want to remove all Whisper Dictation data, including downloaded models and logs?'#13#10#13#10 +
                     'Click Yes to remove everything, or No to keep your data.',
                     mbConfirmation, MB_YESNO);

  if Response = IDYES then
  begin
    // Note: Model files are stored in user's cache directory
    // You can add custom cleanup code here if needed
    MsgBox('Application data will be removed during uninstall.', mbInformation, MB_OK);
  end
  else
  begin
    MsgBox('Application will be removed but your data will be preserved.', mbInformation, MB_OK);
  end;

  Result := True;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  LogDir: String;
  ModelDir: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Optionally clean up user data
    LogDir := ExpandConstant('{localappdata}\WhisperDictation');

    if DirExists(LogDir) then
    begin
      if MsgBox('Remove logs from: ' + LogDir + '?', mbConfirmation, MB_YESNO) = IDYES then
      begin
        DelTree(LogDir, True, True, True);
      end;
    end;

    // Note: Hugging Face model cache is at %USERPROFILE%\.cache\huggingface
    // We don't auto-delete this as other apps may use it
    MsgBox('Uninstall complete!'#13#10#13#10 +
           'Note: Downloaded AI models in %USERPROFILE%\.cache\huggingface were not removed.'#13#10 +
           'You can manually delete this folder if needed to free up space (~150MB).',
           mbInformation, MB_OK);
  end;
end;
