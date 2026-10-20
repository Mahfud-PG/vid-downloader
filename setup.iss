[Setup]
AppName=Vid Downloader
AppVersion=1.0
AppPublisher=ajang berbagi
DefaultDirName={autopf}\Vid Downloader
DefaultGroupName=Vid Downloader
UninstallDisplayIcon={app}\VidDownloader.exe
Compression=lzma2
SolidCompression=yes
OutputDir=C:\vid downloader\installer
OutputBaseFilename=vid downloader
ArchitecturesInstallIn64BitMode=x64
DisableProgramGroupPage=yes

[Files]
Source: "C:\vid downloader\dist\VidDownloader.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Vid Downloader"; Filename: "{app}\VidDownloader.exe"
Name: "{autodesktop}\Vid Downloader"; Filename: "{app}\VidDownloader.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Buat shortcut di Desktop"; GroupDescription: "Ikon Tambahan:"; Flags: unchecked
