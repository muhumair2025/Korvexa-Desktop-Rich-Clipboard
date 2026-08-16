; ===================================================================
; ClipVault — Modern Inno Setup Script
; Organization: Korvexa.app (https://korvexa.app)
; Developer: Muhammad Umair (support@korvexa.app)
; ===================================================================

#define MyAppName "ClipVault"
#define MyAppDisplayName "ClipVault — Windows Rich Clipboard"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Korvexa.app"
#define MyAppDeveloper "Muhammad Umair"
#define MyAppURL "https://korvexa.app"
#define MyAppSupportURL "https://korvexa.app"
#define MyAppUpdatesURL "https://korvexa.app"
#define MyAppSupportEmail "support@korvexa.app"
#define MyAppExeName "ClipVault.exe"
#define MyAppAppId "{{E3796A19-9430-4C94-8177-3B26F227A6D8}"

[Setup]
; --- Application Identity ---
AppId={#MyAppAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppSupportURL}
AppUpdatesURL={#MyAppUpdatesURL}
AppComments=Advanced Windows Rich Clipboard Manager by Korvexa.app (Muhammad Umair)
AppCopyright=Copyright (C) 2026 Korvexa.app. All rights reserved.

; --- Installation Directory & Architecture ---
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
DisableDirPage=no
DisableReadyPage=no
DisableWelcomePage=no

; 64-bit Windows Architecture
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; --- Output & Compression ---
OutputDir=..\dist_installer
OutputBaseFilename=ClipVault_Setup_v1.0.0
SetupIconFile=..\resources\app_icon.ico
UninstallDisplayIcon={app}\resources\app_icon.ico
UninstallDisplayName={#MyAppDisplayName}

; Ultra high-ratio LZMA2 compression
Compression=lzma2/ultra64
InternalCompressLevel=ultra64
SolidCompression=yes

; --- UI and Modern Wizard Styling ---
WizardStyle=modern
WizardImageStretch=yes

; Information & Privacy Pages
LicenseFile=PRIVACY.txt
InfoBeforeFile=ABOUT.txt

; --- Process Management ---
AppMutex=ClipVault_SingleInstance_Mutex_98a72b
CloseApplications=yes
CloseApplicationsFilter=*.exe,*.dll
RestartApplications=no
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; --- Version Information Embedded into Setup ---
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppDisplayName} Installer
VersionInfoCopyright=Copyright (C) 2026 {#MyAppPublisher}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}:"; Flags: unchecked
Name: "startupicon"; Description: "Start ClipVault automatically when Windows starts (Recommended)"; GroupDescription: "System Startup & Integration:"; Flags: unchecked

[Files]
; Primary Executable
Source: "..\dist\ClipVault.exe"; DestDir: "{app}"; Flags: ignoreversion

; Embedded Resources & Custom Icons
Source: "..\resources\*"; DestDir: "{app}\resources"; Flags: ignoreversion recursesubdirs createallsubdirs

; Documentation & Legal Policies
Source: "ABOUT.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "PRIVACY.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu Main Shortcut
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\resources\app_icon.ico"; WorkingDir: "{app}"; Comment: "{#MyAppDisplayName}"

; Desktop Shortcut
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\resources\app_icon.ico"; WorkingDir: "{app}"; Tasks: desktopicon; Comment: "{#MyAppDisplayName}"

; Windows User Startup Shortcut
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\resources\app_icon.ico"; WorkingDir: "{app}"; Tasks: startupicon; Comment: "{#MyAppDisplayName}"

; Website Support Link
Name: "{autoprograms}\Korvexa.app Website"; Filename: "{#MyAppURL}"

[Registry]
; Register App Path for quick Windows Run command (Win+R -> ClipVault)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\App Paths\{#MyAppExeName}"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\App Paths\{#MyAppExeName}"; ValueType: string; ValueName: "Path"; ValueData: "{app}"; Flags: uninsdeletekey

; Application Metadata
Root: HKCU; Subkey: "Software\Korvexa.app\ClipVault"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Korvexa.app\ClipVault"; ValueType: string; ValueName: "Developer"; ValueData: "{#MyAppDeveloper}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Korvexa.app\ClipVault"; ValueType: string; ValueName: "Website"; ValueData: "{#MyAppURL}"; Flags: uninsdeletekey

[Run]
; Option to launch ClipVault immediately after setup completes
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up temporary cache and thumbnails on uninstall
Type: filesandordirs; Name: "{localappdata}\ClipVault\cache"
Type: filesandordirs; Name: "{localappdata}\ClipVault\thumbnails"
Type: filesandordirs; Name: "{localappdata}\ClipVault\logs"

[Code]
// Custom Pascal Scripting for Enhanced Installer Experience

function InitializeSetup(): Boolean;
begin
  Result := True;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir: String;
  MsgRes: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    DataDir := ExpandConstant('{localappdata}\ClipVault');
    if DirExists(DataDir) then
    begin
      MsgRes := MsgBox(
        'Would you like to completely delete your saved clipboard history and local database as well?' + #13#10 + #13#10 +
        'Select "Yes" to remove all data, or "No" to keep your clipboard database for future use.',
        mbConfirmation,
        MB_YESNO or MB_DEFBUTTON2
      );
      if MsgRes = IDYES then
      begin
        DelTree(DataDir, True, True, True);
      end;
    end;
  end;
end;
