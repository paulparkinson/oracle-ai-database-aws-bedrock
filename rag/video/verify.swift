import AppKit
import AVFoundation
import Foundation
let root=URL(fileURLWithPath:FileManager.default.currentDirectoryPath)
let asset=AVURLAsset(url:root.appendingPathComponent("walkthrough.mp4"))
let video=asset.tracks(withMediaType:.video),audio=asset.tracks(withMediaType:.audio)
guard video.count==1,audio.count==1,abs(asset.duration.seconds-180)<0.1,video[0].naturalSize==CGSize(width:1920,height:1080) else {fatalError("Invalid tracks, duration or dimensions")}
for (track,settings) in [(video[0],[kCVPixelBufferPixelFormatTypeKey as String:kCVPixelFormatType_32BGRA] as [String:Any]),(audio[0],[AVFormatIDKey:kAudioFormatLinearPCM] as [String:Any])] {
 let reader=try AVAssetReader(asset:asset),output=AVAssetReaderTrackOutput(track:track,outputSettings:settings)
 reader.add(output);reader.startReading();var samples=0
 while output.copyNextSampleBuffer() != nil {samples+=1}
 guard reader.status == .completed,samples>0 else{fatalError("Complete track decoding failed")}
 print("Decoded \(track.mediaType.rawValue): \(samples) samples")
}
let generator=AVAssetImageGenerator(asset:asset);generator.appliesPreferredTrackTransform=true
generator.maximumSize=CGSize(width:640,height:360)
let sheet=NSImage(size:NSSize(width:1920,height:1440));sheet.lockFocusFlipped(true)
NSColor.black.setFill();NSRect(x:0,y:0,width:1920,height:1440).fill()
for i in 0..<10 {let cg=try generator.copyCGImage(at:CMTime(seconds:Double(i*18+3),preferredTimescale:600),actualTime:nil);NSImage(cgImage:cg,size:NSSize(width:640,height:360)).draw(in:NSRect(x:(i%3)*640,y:(i/3)*360,width:640,height:360),from:.zero,operation:.sourceOver,fraction:1,respectFlipped:true,hints:nil)}
sheet.unlockFocus();var rect=NSRect(origin:.zero,size:sheet.size)
try NSBitmapImageRep(cgImage:sheet.cgImage(forProposedRect:&rect,context:nil,hints:nil)!).representation(using:.png,properties:[:])!.write(to:root.appendingPathComponent(".build/contact-sheet.png"))
print("PASS: complete audio/video decode, 1920×1080, 180 seconds, ten-scene contact sheet.")
