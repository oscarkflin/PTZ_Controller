# Releasing PTZ Controller

## Current state

Do not create releases yet. The repository currently contains a browser-based UI prototype, not a Tauri application or production camera-control implementation.

## Planned release workflow

After the Tauri app is scaffolded and tested, the project will use GitHub Actions to:

1. Run checks on pull requests.
2. Build a Windows installer and a macOS disk image when a version tag is pushed.
3. Create a GitHub Release and attach those installers.

Example version tags: `v0.1.0`, `v0.2.0`, `v1.0.0`.

## macOS distribution

For private early testing, a Mac test build can be installed with a manual security approval. Before distributing widely, the macOS app should be signed with an Apple Developer ID certificate and notarized by Apple. The signing certificate and notarization credentials must be stored as GitHub Actions secrets, never committed to the repository.

## Release checklist

- Confirm manual camera controls on a physical SRG-300SE.
- Confirm joystick mapping and Stop behavior on a Mac.
- Confirm the Windows UI build.
- Update the version and release notes.
- Build installers through GitHub Actions.
- Install each generated installer on a clean test machine.
- Publish the GitHub Release only after the checks pass.
