# PhantomResume Android 1.3

An Android companion to the Windows desktop workbench. One APK bundles its Python
runtime, document libraries, 38 tools and an animated touch interface. No Python
installation, account or remote processing server is required.

## Use

Install PhantomResume Android.apk on Android 8 or newer, on an ARM64 phone or an
x86-64 device/emulator. Open the app and use the menu to choose a tool. Try a sample
creates a fictional Test Candidate document. Choose imports through Android's
file picker; the app copies each input into its private storage.

Run the tool, then use Saved files to save a document through Android's file picker,
share it through the Android chooser, or export the whole run as a ZIP. Export
important results before uninstalling: uninstalling removes private app data.
Only the explicitly chosen file is shared. No application submissions are made.

All 15 injection channels can be selected together or independently. Audio and
font metadata channels require compatible embedded assets; absent assets are
reported as skipped. The font fixture tool can create an embedded test font.
The source payload strings are retained from the desktop project.

## Platform differences

- Android web inspection reads public server HTML. It does not run page JavaScript
  or produce a browser screenshot. Use Windows for rendered Chromium inspection.
- QR inspection uses Android's ZXing decoder instead of desktop ZBar.
- PDF export uses the portable renderer. Word layout can reflow; inspect complex
  tables and non-Latin text before using the exported PDF.
- Android file picking imports copies. Batch processing accepts multiple DOCX
  files, rather than requiring direct access to a desktop folder.
- Back or Close app removes the app task and exits its own UI process, releasing
  its WebView bindings as well as the worker. Home backgrounds the app instead.

## Resources and shutdown

One bound service in a separate process runs one task at a time. On completion,
cancellation, Back/Close or removal of the app task, the service stops and its
process is terminated. There is no startup receiver, resident foreground service,
periodic scheduler or local HTTP server. The main screen is a local WebView with native Run/Cancel controls. The launch
screen plays a short native animation once. Setup and results have separate tabs.
The active task keeps the display awake; that flag clears when the task ends.

Animations run briefly; the spinner runs only during work. Reduce motion is in
the menu, and animation pauses when the app is not visible. Result previews are
bounded; full reports remain in each run's folder. Runs time out after 15 minutes.
Interrupted output folders retain INCOMPLETE.txt. Input copies are not modified.

This is not a guarantee against every OS, storage or parser failure. The system
may stop a backgrounded app. Save needed results to a user-selected location.

## Code protection

The APK is signed with a locally generated release key. Java code is optimized
and obfuscated with R8; Python application modules are packaged as bytecode.
Neither signing nor bytecode prevents reverse engineering. The Windows build's
native core compilation is stronger protection than this Android bytecode layer.
No signing key, password, personal resume or user account session is bundled.

## Build

Use JDK 17, Gradle 8.11.1, Android SDK 35 and Python 3.12. Set the SDK location via
ANDROID_HOME or local.properties. Set PHANTOM_BUILD_PYTHON to the build Python
executable when it is not available as `python` on PATH. Dependencies are pinned
in app/build.gradle. Run `gradle assembleDebug` for a local development build.

For `gradle assembleRelease`, set PHANTOM_KEYSTORE, PHANTOM_STORE_PASSWORD and
PHANTOM_KEY_PASSWORD. The key alias is phantomresume. Keep the release keystore
and its credentials private and back them up; future updates need the same key.
The release uses AGP 8.9.2 and Chaquopy 17.2.0. Source and third-party notices are
provided separately from the APK.

The local acceptance harness can be launched with the activity intent extra
`selftest=true`. It uses synthetic files and a localhost page, writes its results
to the app-specific external-files directory, and logs synthetic check results.
It never uses a real resume or submits to a job portal.

## 1.3 update

PDF, embedded-font and FLAC/WebM repairs are merged from the original project.
Addon verification runs seven local synthetic checks. Addon source is bundled,
but its API still has no configured document channels. This does not establish
live ATS payload recovery. See the current Build verification.json for packaged
app checks; older screenshots and results are not evidence for this build.
