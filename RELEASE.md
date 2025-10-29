# Release Process

This project uses GitHub Actions to automatically build and release Windows installers.

## Automated Release (Recommended)

### Step 1: Prepare for Release

Make sure all changes are committed and pushed:

```bash
git add .
git commit -m "Prepare for release v1.0.0"
git push
```

### Step 2: Create and Push a Version Tag

```bash
# Create a version tag (use semantic versioning)
git tag v1.0.0

# Push the tag to GitHub
git push origin v1.0.0
```

### Step 3: Wait for GitHub Actions

- GitHub Actions will automatically:
  1. Build the executables with PyInstaller
  2. Download Ollama installer
  3. Compile the Inno Setup installer
  4. Create a GitHub Release
  5. Upload `WhisperDictation_Setup.exe`

- This takes approximately **10-15 minutes**

### Step 4: Verify the Release

1. Go to: `https://github.com/matdac12/transcriber/releases`
2. You should see your new release with the installer attached
3. Test the download link

## Manual Build (For Testing)

If you want to build the installer locally before releasing:

### Prerequisites

1. Install Python 3.11
2. Install dependencies: `pip install pyinstaller faster-whisper soundfile scipy av ttkbootstrap requests pystray pillow sounddevice pyperclip keyboard numpy`
3. Install [Inno Setup](https://jrsoftware.org/isinfo.php)

### Build Steps

```bash
# 1. Download Ollama installer (optional, if you want to bundle it)
python download_ollama_installer.py

# 2. Build executables
python build_installer.py

# 3. Compile installer with Inno Setup
# Right-click installer.iss and select "Compile"
# Or use command line:
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss

# 4. Installer will be in: installer_output/WhisperDictation_Setup.exe
```

## Version Numbering

Use [Semantic Versioning](https://semver.org/):

- **v1.0.0** - Major release (breaking changes)
- **v1.1.0** - Minor release (new features)
- **v1.0.1** - Patch release (bug fixes)

## Troubleshooting

### GitHub Actions fails

1. Check the Actions tab: `https://github.com/matdac12/transcriber/actions`
2. Click on the failed workflow to see logs
3. Common issues:
   - Missing dependencies
   - Ollama download timeout
   - Inno Setup compilation errors

### Delete a tag (if needed)

```bash
# Delete local tag
git tag -d v1.0.0

# Delete remote tag
git push origin :refs/tags/v1.0.0
```

## First Release Checklist

- [ ] All features tested locally
- [ ] Version number decided
- [ ] CHANGELOG.md updated (optional)
- [ ] Tag created and pushed
- [ ] GitHub Actions build successful
- [ ] Release installer downloaded and tested
- [ ] Release notes reviewed

## Notes

- The workflow only triggers on tags starting with `v` (e.g., `v1.0.0`, `v2.3.1`)
- Regular commits to `main` branch do NOT trigger builds
- Ollama installer (~300MB) is downloaded during the build, not stored in git
- Models are NOT bundled - they download on first app use
