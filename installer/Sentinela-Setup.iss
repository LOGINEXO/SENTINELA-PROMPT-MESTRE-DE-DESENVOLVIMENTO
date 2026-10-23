#define MyAppName "Sentinela"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Projeto Sentinela"
#define MyAppURL "https://github.com/LOGINEXO/SENTINELA-PROMPT-MESTRE-DE-DESENVOLVIMENTO"

[Setup]
AppId={{A1D9202D-7E6F-4B36-9B6E-5E8F0A6F8D21}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\Sentinela
DefaultGroupName=Sentinela
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=output
OutputBaseFilename=Sentinela-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
Uninstallable=yes
SetupLogging=yes
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Files]
Source: "install-sentinela.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "start-sentinela.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "LEIA-ME.txt"; DestDir: "{app}"; Flags: ignoreversion

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos:"; Flags: unchecked

[Icons]
Name: "{autoprograms}\Sentinela\Instalar e reparar dependências"; Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\install-sentinela.ps1"""; WorkingDir: "{app}"
Name: "{autoprograms}\Sentinela\Abrir Sentinela"; Filename: "powershell.exe"; Parameters: "-NoExit -NoProfile -ExecutionPolicy Bypass -File ""{app}\start-sentinela.ps1"""; WorkingDir: "{app}"
Name: "{autodesktop}\Sentinela"; Filename: "powershell.exe"; Parameters: "-NoExit -NoProfile -ExecutionPolicy Bypass -File ""{app}\start-sentinela.ps1"""; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "powershell.exe"; Parameters: "-NoExit -NoProfile -ExecutionPolicy Bypass -File ""{app}\install-sentinela.ps1"""; WorkingDir: "{app}"; Description: "Instalar dependências e preparar o Sentinela"; Flags: postinstall waituntilterminated
