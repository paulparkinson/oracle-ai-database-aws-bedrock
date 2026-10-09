# Narrated RAG walkthrough

`scenes.json` defines seven 18-second scenes (126 seconds total), exact visual sources and three six-second narration/caption cues per scene. Screenshots are captured from live successful browser requests; they are not generated application results. Code scenes read the current repository source. `narration.txt`, SRT and VTT are generated from the same cues.

On macOS, from this directory:

```sh
swift build.swift
swift verify.swift
bash ../../skills/video-blog-walkthrough/scripts/audit_video.sh "$PWD/walkthrough.mp4" walkthrough.srt ../blog.html
```

Requires Apple's Swift/AppKit/AVFoundation and `say`; no paid voice service. If the default SDK is newer than the compiler, select an installed matching SDK explicitly with `swift -sdk /path/to/matching/MacOSX.sdk build.swift`. Rendering replaces only this directory's generated MP4/poster/captions and ignored `.build` intermediates. Refresh live screenshots after implementation changes. Do not capture `.env`, wallets, browser accounts or private endpoint details.
