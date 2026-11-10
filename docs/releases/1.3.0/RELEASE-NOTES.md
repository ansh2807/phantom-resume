PhantomResume 1.3.0 development release updates the Windows and Android apps with the original project's PDF, embedded-font and FLAC/WebM repairs. It includes addon modules and a local Addon verification tool, while retaining the animated interfaces and existing tools.

- Windows EXE: 78 packaged acceptance checks passed, including worker/browser cancellation and shutdown.
- Android APK: 40 synthetic checks passed on an ARM64 phone; signed with the existing release certificate and tested as an in-place update. Back leaves no app process or service.
- Repository: 13 local regression tests passed. Public-file privacy checks passed.
- Build sources are under apps/windows and apps/android; verification records are under docs/releases/1.3.0.

The Windows executable is an unsigned local build. Android supports Android 8+ with ARM64 and x86_64 packaged; x86_64 was not device-tested in this update.

The historical source audit recorded 166 passing cases and seven not run. It was not rerun against these apps. The addon API has no document channels configured; no live ATS effectiveness is established. Four planned modules remain unimplemented. See the repository's release documentation for full limits.

No personal resumes, databases, signing keys or credentials are included. Checksums accompany the downloads. Native compilation and bytecode do not make either app impossible to reverse engineer.
