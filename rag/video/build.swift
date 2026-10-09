import AppKit
import AVFoundation
import CoreVideo
import Foundation

struct Scene: Decodable {let title:String;let kind:String;let body:String?;let file:String?;let marker:String?;let lines:Int?;let cues:[String]}
let fm=FileManager.default, root=URL(fileURLWithPath:fm.currentDirectoryPath)
let scenes=try JSONDecoder().decode([Scene].self,from:Data(contentsOf:root.appendingPathComponent("scenes.json")))
let work=root.appendingPathComponent(".build")
try fm.createDirectory(at:work,withIntermediateDirectories:true)
let out=root.appendingPathComponent("walkthrough.mp4"), silent=work.appendingPathComponent("silent.mp4")
for url in [out,silent] where fm.fileExists(atPath:url.path) {try fm.removeItem(at:url)}
let width=1920,height=1080,fps:Int32=24, sceneSeconds=18.0
func stamp(_ n:Int,_ sep:String)->String {String(format:"%02d:%02d:%02d%@000",n/3600,n/60%60,n%60,sep)}
func wrap(_ t:String)->String {var lines=[String](),line="";for w in t.split(separator:" "){if line.count+w.count+1>48 {lines.append(line);line=""};line+=(line.isEmpty ? "":" ")+w};lines.append(line);return lines.joined(separator:"\n")}
func text(_ t:String,_ rect:NSRect,_ size:CGFloat,_ color:NSColor = .white,_ mono:Bool=false){let p=NSMutableParagraphStyle();p.lineSpacing=7;t.draw(with:rect,options:[.usesLineFragmentOrigin],attributes:[.font:mono ? NSFont.monospacedSystemFont(ofSize:size,weight:.regular):NSFont.systemFont(ofSize:size,weight:.medium),.foregroundColor:color,.paragraphStyle:p])}
func render(_ s:Scene)->CGImage {
 let image=NSImage(size:NSSize(width:width,height:height));image.lockFocusFlipped(true)
 NSColor(calibratedRed:0.08,green:0.13,blue:0.15,alpha:1).setFill();NSRect(x:0,y:0,width:width,height:height).fill()
 text("ORACLE AI DATABASE × AMAZON BEDROCK",NSRect(x:70,y:38,width:1750,height:40),24,NSColor.systemOrange)
 text(s.title,NSRect(x:70,y:100,width:1750,height:90),48)
 if s.kind=="image" {
  let image=NSImage(contentsOf:root.appendingPathComponent(s.file!))!
  // Frame the real captured answer/evidence card, removing redundant page header.
  var rect=NSRect(origin:.zero,size:image.size);let cg=image.cgImage(forProposedRect:&rect,context:nil,hints:nil)!
  let crop=cg.cropping(to:CGRect(x:100,y:480,width:cg.width-200,height:cg.height-480))!
  let shown=NSImage(cgImage:crop,size:NSSize(width:crop.width,height:crop.height))
  let scale=min(1700/shown.size.width,760/shown.size.height)
  shown.draw(in:NSRect(x:CGFloat(width)/2-shown.size.width*scale/2,y:210,width:shown.size.width*scale,height:shown.size.height*scale),from:.zero,operation:.sourceOver,fraction:1,respectFlipped:true,hints:nil)
 } else {
  var body=s.body ?? ""
  if s.kind=="code" {let lines=try! String(contentsOf:root.appendingPathComponent(s.file!),encoding:.utf8).components(separatedBy:"\n");let start=lines.firstIndex(where:{$0.contains(s.marker!)})!;body=lines[start..<min(lines.count,start+s.lines!)].joined(separator:"\n")}
  text(body,NSRect(x:80,y:230,width:1760,height:730),s.kind=="code" ? 27:37,.white,s.kind=="code")
 }
 text("Live captures + repository source · Synthetic fixture · No persistent database writes",NSRect(x:70,y:1015,width:1750,height:40),23,NSColor.lightGray)
 image.unlockFocus();var r=NSRect(origin:.zero,size:image.size);return image.cgImage(forProposedRect:&r,context:nil,hints:nil)!
}
let frames=scenes.map(render)
for (i,cg) in frames.enumerated(){let rep=NSBitmapImageRep(cgImage:cg);try rep.representation(using:.png,properties:[:])!.write(to:work.appendingPathComponent("scene-\(i).png"))}
try NSBitmapImageRep(cgImage:frames[0]).representation(using:.png,properties:[:])!.write(to:root.appendingPathComponent("poster.png"))
let writer=try AVAssetWriter(outputURL:silent,fileType:.mp4)
let input=AVAssetWriterInput(mediaType:.video,outputSettings:[AVVideoCodecKey:AVVideoCodecType.h264,AVVideoWidthKey:width,AVVideoHeightKey:height])
let attrs:[String:Any]=[kCVPixelBufferPixelFormatTypeKey as String:kCVPixelFormatType_32ARGB,kCVPixelBufferWidthKey as String:width,kCVPixelBufferHeightKey as String:height]
let adaptor=AVAssetWriterInputPixelBufferAdaptor(assetWriterInput:input,sourcePixelBufferAttributes:attrs)
writer.add(input);writer.startWriting();writer.startSession(atSourceTime:.zero)
for frame in 0..<Int(Double(scenes.count)*sceneSeconds*Double(fps)) {
 while !input.isReadyForMoreMediaData {Thread.sleep(forTimeInterval:0.002)}
 var b:CVPixelBuffer?;CVPixelBufferCreate(kCFAllocatorDefault,width,height,kCVPixelFormatType_32ARGB,attrs as CFDictionary,&b)
 CVPixelBufferLockBaseAddress(b!,[])
 let context=CGContext(data:CVPixelBufferGetBaseAddress(b!),width:width,height:height,bitsPerComponent:8,bytesPerRow:CVPixelBufferGetBytesPerRow(b!),space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.noneSkipFirst.rawValue)!
 context.draw(frames[frame/Int(sceneSeconds*Double(fps))],in:CGRect(x:0,y:0,width:width,height:height));CVPixelBufferUnlockBaseAddress(b!,[])
 guard adaptor.append(b!,withPresentationTime:CMTime(value:Int64(frame),timescale:fps)) else {fatalError("Video frame failed")}
}
input.markAsFinished();let sem=DispatchSemaphore(value:0);writer.finishWriting{sem.signal()};sem.wait();guard writer.status == .completed else {throw writer.error!}
let composition=AVMutableComposition();let v=composition.addMutableTrack(withMediaType:.video,preferredTrackID:kCMPersistentTrackID_Invalid)!
let silentAsset=AVURLAsset(url:silent);try v.insertTimeRange(CMTimeRange(start:.zero,duration:silentAsset.duration),of:silentAsset.tracks(withMediaType:.video)[0],at:.zero)
let a=composition.addMutableTrack(withMediaType:.audio,preferredTrackID:kCMPersistentTrackID_Invalid)!
var srt="",vtt="WEBVTT\n\n",narration=""
for (i,s) in scenes.enumerated(){for (j,cue) in s.cues.enumerated(){
 let start=i*18+j*6, audio=work.appendingPathComponent("cue-\(i)-\(j).aiff")
 let p=Process();p.executableURL=URL(fileURLWithPath:"/usr/bin/say");p.arguments=["-r","165","-o",audio.path,cue];try p.run();p.waitUntilExit();guard p.terminationStatus==0 else{fatalError("Narration failed")}
 let asset=AVURLAsset(url:audio);guard asset.duration.seconds<=6 else{fatalError("Cue exceeds six seconds: \(cue)")}
 try a.insertTimeRange(CMTimeRange(start:.zero,duration:asset.duration),of:asset.tracks(withMediaType:.audio)[0],at:CMTime(seconds:Double(start),preferredTimescale:600))
 let content=wrap(cue);srt+="\(i*3+j+1)\n\(stamp(start,",")) --> \(stamp(start+6,","))\n\(content)\n\n";vtt+="\(stamp(start,".")) --> \(stamp(start+6,"."))\n\(content)\n\n";narration+="\(start)s: \(cue)\n"
}}
try srt.write(to:root.appendingPathComponent("walkthrough.srt"),atomically:true,encoding:.utf8)
try vtt.write(to:root.appendingPathComponent("walkthrough.vtt"),atomically:true,encoding:.utf8)
try narration.write(to:root.appendingPathComponent("narration.txt"),atomically:true,encoding:.utf8)
let exporter=AVAssetExportSession(asset:composition,presetName:AVAssetExportPresetHighestQuality)!
exporter.outputURL=out;exporter.outputFileType = .mp4
let done=DispatchSemaphore(value:0);exporter.exportAsynchronously{done.signal()};done.wait();guard exporter.status == .completed else{throw exporter.error!}
print("Created 1920x1080 narrated walkthrough, \(scenes.count*18) seconds, with SRT/VTT captions.")
