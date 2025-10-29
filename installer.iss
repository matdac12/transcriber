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
#define OllamaInstaller "installer_resources\OllamaSetup.exe"
#define OllamaModelScript "installer_resources\install_ollama_models.py"
#define WhisperModelScript "download_models_installer.py"

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
UninstallDisplayIcon={app}\WhisperDictation\{#MyAppExeName}

; Directory and group settings
DisableProgramGroupPage=yes
DisableReadyPage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create desktop shortcut for Whisper Dictation (Systray)"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "desktopicon_transcriber"; Description: "Create desktop shortcut for File Transcriber"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; Check: not IsAdminInstallMode
Name: "startup"; Description: "Start Whisper Dictation automatically when Windows starts"; GroupDescription: "Auto-start:"; Flags: unchecked
Name: "installollama"; Description: "Install Ollama for AI-powered summary generation (recommended, ~300MB download)"; GroupDescription: "AI Features:"

[Files]
; Main executables (--onedir mode: entire folders)
Source: "dist\WhisperDictation\*"; DestDir: "{app}\WhisperDictation"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\FileTranscriber\*"; DestDir: "{app}\FileTranscriber"; Flags: ignoreversion recursesubdirs createallsubdirs

; Support files
Source: "dist\DictationApp\run_systray.vbs"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\DictationApp\Start_Dictation.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\DictationApp\README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "dist\DictationApp\QUICKSTART.txt"; DestDir: "{app}"; Flags: ignoreversion

; Ollama installer and scripts (only if task is selected)
Source: "{#OllamaInstaller}"; DestDir: "{tmp}"; Flags: deleteafterinstall; Tasks: installollama; Check: FileExists(ExpandConstant('{#OllamaInstaller}'))
Source: "{#OllamaModelScript}"; DestDir: "{tmp}"; Flags: deleteafterinstall; Tasks: installollama

; Whisper model download script (removed - models download on first app use instead)

[Icons]
; Start Menu shortcuts
Name: "{group}\Whisper Dictation (Systray)"; Filename: "{app}\WhisperDictation\{#MyAppExeName}"
Name: "{group}\File Transcriber"; Filename: "{app}\FileTranscriber\{#MyAppTranscriberName}"
Name: "{group}\Quick Start Guide"; Filename: "{app}\QUICKSTART.txt"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Desktop shortcuts (optional)
Name: "{autodesktop}\Whisper Dictation"; Filename: "{app}\WhisperDictation\{#MyAppExeName}"; Tasks: desktopicon
Name: "{autodesktop}\File Transcriber"; Filename: "{app}\FileTranscriber\{#MyAppTranscriberName}"; Tasks: desktopicon_transcriber

; Quick Launch shortcut (optional, for older Windows)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\Whisper Dictation"; Filename: "{app}\WhisperDictation\{#MyAppExeName}"; Tasks: quicklaunchicon

; Startup shortcut (optional)
Name: "{userstartup}\Whisper Dictation"; Filename: "{app}\WhisperDictation\{#MyAppExeName}"; Tasks: startup

[Run]
; Option to launch the app after installation
Filename: "{app}\WhisperDictation\{#MyAppExeName}"; Description: "{cm:LaunchProgram,Whisper Dictation}"; Flags: nowait postinstall skipifsilent

[Code]
var
  OllamaInstallNeeded: Boolean;
  ModelSelectionPage: TInputOptionWizardPage;
  TinyModelCheckBox: TNewCheckBox;
  BaseModelCheckBox: TNewCheckBox;
  SmallModelCheckBox: TNewCheckBox;

procedure CreateModelSelectionPage();
var
  DescLabel: TNewStaticText;
  YPos: Integer;
begin
  // Create custom page for model selection
  ModelSelectionPage := CreateInputOptionPage(
    wpSelectTasks,
    'Select Whisper Models',
    'Choose which AI models to download',
    'Select one or more models to download. You can download additional models later from the File Transcriber app.',
    False,
    False
  );

  // Add description labels with size info
  YPos := 10;

  // Tiny model checkbox
  TinyModelCheckBox := TNewCheckBox.Create(WizardForm);
  TinyModelCheckBox.Parent := ModelSelectionPage.Surface;
  TinyModelCheckBox.Caption := 'Tiny (~39 MB) - Fastest, basic accuracy';
  TinyModelCheckBox.Left := ScaleX(0);
  TinyModelCheckBox.Top := ScaleY(YPos);
  TinyModelCheckBox.Width := ModelSelectionPage.SurfaceWidth;
  TinyModelCheckBox.Height := ScaleY(17);
  TinyModelCheckBox.Checked := True;  // Default: tiny checked
  YPos := YPos + 30;

  // Base model checkbox
  BaseModelCheckBox := TNewCheckBox.Create(WizardForm);
  BaseModelCheckBox.Parent := ModelSelectionPage.Surface;
  BaseModelCheckBox.Caption := 'Base (~141 MB) - Recommended, good balance';
  BaseModelCheckBox.Left := ScaleX(0);
  BaseModelCheckBox.Top := ScaleY(YPos);
  BaseModelCheckBox.Width := ModelSelectionPage.SurfaceWidth;
  BaseModelCheckBox.Height := ScaleY(17);
  BaseModelCheckBox.Checked := True;  // Default: base checked
  YPos := YPos + 30;

  // Small model checkbox
  SmallModelCheckBox := TNewCheckBox.Create(WizardForm);
  SmallModelCheckBox.Parent := ModelSelectionPage.Surface;
  SmallModelCheckBox.Caption := 'Small (~461 MB) - Better accuracy, slower';
  SmallModelCheckBox.Left := ScaleX(0);
  SmallModelCheckBox.Top := ScaleY(YPos);
  SmallModelCheckBox.Width := ModelSelectionPage.SurfaceWidth;
  SmallModelCheckBox.Height := ScaleY(17);
  SmallModelCheckBox.Checked := False;  // Default: small not checked
  YPos := YPos + 40;

  // Add note at bottom
  DescLabel := TNewStaticText.Create(WizardForm);
  DescLabel.Parent := ModelSelectionPage.Surface;
  DescLabel.Caption := 'Note: Models are downloaded once and stored permanently in the installation directory.';
  DescLabel.Left := ScaleX(0);
  DescLabel.Top := ScaleY(YPos);
  DescLabel.Width := ModelSelectionPage.SurfaceWidth;
  DescLabel.AutoSize := True;
  DescLabel.WordWrap := True;
end;

function IsOllamaInstalled(): Boolean;
var
  ResultCode: Integer;
  OllamaPath: String;
begin
  Result := False;

  // Check if ollama.exe exists in common locations
  // Method 1: Check PATH by running ollama --version
  if Exec('cmd.exe', '/C ollama --version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    if ResultCode = 0 then
    begin
      Log('Ollama found via PATH');
      Result := True;
      Exit;
    end;
  end;

  // Method 2: Check common installation directories
  OllamaPath := ExpandConstant('{localappdata}\Programs\Ollama\ollama.exe');
  if FileExists(OllamaPath) then
  begin
    Log('Ollama found at: ' + OllamaPath);
    Result := True;
    Exit;
  end;

  OllamaPath := ExpandConstant('{pf}\Ollama\ollama.exe');
  if FileExists(OllamaPath) then
  begin
    Log('Ollama found at: ' + OllamaPath);
    Result := True;
    Exit;
  end;

  Log('Ollama not found');
end;

procedure InitializeWizard();
begin
  // Model selection page removed - models download automatically on first use
  // This avoids requiring Python on user's system during installation
end;

function InitializeSetup(): Boolean;
var
  OllamaMessage: String;
begin
  Result := True;

  // Check if Ollama is already installed
  if IsOllamaInstalled() then
  begin
    OllamaInstallNeeded := False;
    OllamaMessage := 'Ollama already installed ✓';
  end
  else
  begin
    OllamaInstallNeeded := True;
    OllamaMessage := 'Ollama will be installed';
  end;

  // Show welcome message
  MsgBox('Welcome to Whisper Dictation & File Transcriber Setup!'#13#10#13#10 +
         'This application uses AI-powered speech recognition to:'#13#10 +
         '• Convert speech to text in real-time'#13#10 +
         '• Transcribe audio files to text'#13#10 +
         '• Generate AI-powered summaries (with Ollama)'#13#10#13#10 +
         'Note: AI models will download automatically when you first use the app.'#13#10 +
         OllamaMessage + #13#10#13#10 +
         'Internet connection required on first use.',
         mbInformation, MB_OK);
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  OllamaSetupPath: String;
  OllamaScriptPath: String;
  PythonExe: String;
  OllamaInstalled: Boolean;
begin
  if CurStep = ssPostInstall then
  begin
    // NOTE: Whisper models are NOT downloaded during installation
    // They will be downloaded automatically when the apps first need them
    // This avoids requiring Python to be installed on the user's system

    // Install/configure Ollama if task is selected
    if WizardIsTaskSelected('installollama') then
    begin
      WizardForm.ProgressGauge.Style := npbstMarquee;
      OllamaInstalled := False;

      // Check if Ollama needs to be installed
      if OllamaInstallNeeded then
      begin
        // Ollama not installed, need to install it
        OllamaSetupPath := ExpandConstant('{tmp}\OllamaSetup.exe');

        if FileExists(OllamaSetupPath) then
        begin
          WizardForm.StatusLabel.Caption := 'Installing Ollama...';
          Log('Installing Ollama...');

          // Run Ollama installer silently
          if Exec(OllamaSetupPath, '/SILENT /NORESTART', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
          begin
            if ResultCode = 0 then
            begin
              Log('Ollama installed successfully');
              OllamaInstalled := True;
            end
            else
            begin
              Log('Ollama installation failed with code: ' + IntToStr(ResultCode));
              MsgBox('Ollama installation failed. AI summaries will not be available.'#13#10 +
                     'You can install Ollama manually from https://ollama.com',
                     mbError, MB_OK);
              WizardForm.ProgressGauge.Style := npbstNormal;
              Exit;
            end;
          end
          else
          begin
            Log('Failed to execute Ollama installer');
            MsgBox('Could not run Ollama installer. AI summaries will not be available.',
                   mbError, MB_OK);
            WizardForm.ProgressGauge.Style := npbstNormal;
            Exit;
          end;
        end;
      end
      else
      begin
        // Ollama already installed
        Log('Ollama already installed, skipping installation');
        WizardForm.StatusLabel.Caption := 'Ollama already installed ✓';
        OllamaInstalled := True;
      end;

      // If Ollama is installed (either just now or already), download models
      if OllamaInstalled then
      begin
        OllamaScriptPath := ExpandConstant('{tmp}\install_ollama_models.py');

        if FileExists(OllamaScriptPath) then
        begin
          WizardForm.StatusLabel.Caption := 'Checking Ollama models...';

          // Try to find Python
          if RegQueryStringValue(HKEY_CURRENT_USER, 'Software\Python\PythonCore\3.12\InstallPath', '', PythonExe) or
             RegQueryStringValue(HKEY_CURRENT_USER, 'Software\Python\PythonCore\3.11\InstallPath', '', PythonExe) or
             RegQueryStringValue(HKEY_LOCAL_MACHINE, 'Software\Python\PythonCore\3.12\InstallPath', '', PythonExe) or
             RegQueryStringValue(HKEY_LOCAL_MACHINE, 'Software\Python\PythonCore\3.11\InstallPath', '', PythonExe) then
          begin
            PythonExe := AddBackslash(PythonExe) + 'python.exe';
          end
          else
          begin
            // Try common python command
            PythonExe := 'python';
          end;

          // Run the model download/check script
          if Exec(PythonExe, '"' + OllamaScriptPath + '"', '', SW_SHOW, ewWaitUntilTerminated, ResultCode) then
          begin
            if ResultCode = 0 then
            begin
              Log('Ollama models configured successfully');
              MsgBox('Ollama and AI models are ready!'#13#10 +
                     'Summary generation is now available in the File Transcriber.',
                     mbInformation, MB_OK);
            end
            else
            begin
              Log('Ollama model configuration failed with code: ' + IntToStr(ResultCode));
              MsgBox('Ollama is installed but model setup failed.'#13#10 +
                     'You can download models later by running:'#13#10 +
                     'ollama pull deepseek-r1:1.5b',
                     mbInformation, MB_OK);
            end;
          end
          else
          begin
            Log('Failed to execute model script');
            MsgBox('Could not run model setup script.'#13#10 +
                   'You can download models later by running:'#13#10 +
                   'ollama pull deepseek-r1:1.5b',
                   mbInformation, MB_OK);
          end;
        end;
      end;

      // Reset progress bar
      WizardForm.ProgressGauge.Style := npbstNormal;
    end;
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
