# Narrated RAG walkthrough

`scenes.json` defines ten 18-second scenes (180 seconds total), exact visual sources and three six-second narration/caption cues per scene. This is an edited screenshot-and-source walkthrough, not continuous screen recording. Result captures come from the earlier verified live requests; the start screen was refreshed for this revision. No results are generated or fabricated. NL2SQL remains illustrative, not demonstrated. Code scenes read the current repository source. `narration.txt`, SRT and VTT are generated from the same cues.

On macOS, from this directory:

```sh
swift build.swift
swift verify.swift
bash ../../skills/video-blog-walkthrough/scripts/audit_video.sh "$PWD/walkthrough.mp4" walkthrough.srt ../blog.html
```

Requires Apple's Swift/AppKit/AVFoundation and `say`; no paid voice service. If the default SDK is newer than the compiler, select an installed matching SDK explicitly with `swift -sdk /path/to/matching/MacOSX.sdk build.swift`. Rendering replaces only this directory's generated MP4/poster/captions and ignored `.build` intermediates. Refresh live screenshots after implementation changes. Do not capture `.env`, wallets, browser accounts or private endpoint details.
