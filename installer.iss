; StockAlert Inno Setup Script
; Professional installer with desktop shortcut and launch-after-install options

#define MyAppName "StockAlert"
#define MyAppVersion "3.0.0"
#define MyAppPublisher "CUSHLABS.AI"
#define MyAppURL "https://cushlabs.ai"
#define MyAppExeName "StockAlert.exe"
#define MyAppDescription "Commercial-grade stock price monitoring with Windows notifications"

[Setup]
; Unique application ID - DO NOT CHANGE after first release
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
; Allow user to disable Start Menu folder
AllowNoIcons=yes
; Skip license and readme pages for faster install
DisableDirPage=yes
DisableProgramGroupPage=yes
; Output settings
OutputDir=dist
OutputBaseFilename=StockAlert-{#MyAppVersion}-Setup
; Compression
Compression=lzma2/ultra64
SolidCompression=yes
; Modern look
WizardStyle=modern
; Icon
SetupIconFile=stock_alert.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
; Privileges - install for current user by default (no admin needed)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; Minimum Windows version (Windows 10)
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
; Desktop shortcut - checked by default
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
; Start Menu shortcut - checked by default
Name: "startmenu"; Description: "Create a Start Menu shortcut"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Main application files from cx_Freeze build
Source: "build\exe.win-amd64-3.12\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Environment template for user configuration
Source: ".env.example"; DestDir: "{app}"; Flags: ignoreversion
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
; Start Menu shortcut
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startmenu
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"; Tasks: startmenu
; Desktop shortcut
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Launch after install - checked by default
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up config and logs on uninstall (optional - user data)
Type: files; Name: "{app}\config.json"
Type: files; Name: "{app}\*.log"
Type: dirifempty; Name: "{app}"

[Code]
// Custom code for additional functionality

function InitializeSetup(): Boolean;
begin
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Post-install actions if needed
  end;
end;
