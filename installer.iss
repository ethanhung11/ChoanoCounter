#define MyVersion GetEnv("APP_VERSION")

[Setup]
AppName=ChoanoCounter
AppVersion={#MyVersion}
DefaultDirName={autopf}\ChoanoCounter
DefaultGroupName=ChoanoCounter
OutputDir=Output
OutputBaseFilename=ChoanoCounter-{#MyVersion}-Windows-Setup

[Files]
Source: "dist\ChoanoCounter\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\ChoanoCounter"; Filename: "{app}\ChoanoCounter.exe"
Name: "{autodesktop}\ChoanoCounter"; Filename: "{app}\ChoanoCounter.exe"