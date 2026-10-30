package com.lifecircle.storage;

import com.lifecircle.common.result.Result;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.servlet.mvc.method.annotation.StreamingResponseBody;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.zip.*;

@RestController
@RequestMapping("/api/files")
public class LocalFileController {
    private final LocalFileService service;
    private final ChunkUploadService chunks;
    @org.springframework.beans.factory.annotation.Autowired private DownloadCapacity downloadCapacity;
    public LocalFileController(LocalFileService service, ChunkUploadService chunks) { this.service=service; this.chunks=chunks; }
    @PostMapping("/upload") public Result<LocalFileService.FileInfo> upload(@RequestParam("file") MultipartFile file) throws IOException { return Result.ok(service.upload(file)); }
    @GetMapping public Result<List<LocalFileService.FileInfo>> list() throws IOException { return Result.ok(service.list()); }
    @GetMapping("/config") public Result<Map<String,Object>> config() { return Result.ok(Map.of("mode",service.mode(),"chunkSize",5*1024*1024,"maxFileSize",ChunkUploadService.MAX_SIZE)); }
    @GetMapping("/download-stats") public Result<Map<String,Object>> downloadStats() { return Result.ok(downloadCapacity.snapshot()); }
    @PostMapping("/uploads") public Result<ChunkUploadService.Session> init(@RequestBody ChunkUploadService.Init request) throws IOException { return Result.ok(chunks.init(request)); }
    @GetMapping("/uploads/{id}") public Result<ChunkUploadService.Status> status(@PathVariable("id") String id) throws IOException { return Result.ok(chunks.status(id)); }
    @PutMapping("/uploads/{id}/chunks/{index}") public Result<Void> chunk(@PathVariable("id") String id, @PathVariable("index") int index,
        @RequestParam("file") MultipartFile file, @RequestParam("sha256") String sha256) throws IOException { chunks.chunk(id,index,file,sha256); return Result.ok(); }
    @PostMapping("/uploads/{id}/complete") public Result<LocalFileService.FileInfo> complete(@PathVariable("id") String id) throws IOException { return Result.ok(chunks.complete(id)); }
    @DeleteMapping("/uploads/{id}") public Result<Void> cancel(@PathVariable("id") String id) throws IOException { chunks.cancel(id); return Result.ok(); }
    @PostMapping("/batch") public Result<List<LocalFileService.BatchItem>> batch(@RequestParam("files") MultipartFile[] files) throws IOException { return Result.ok(service.batch(files)); }

    record Range(long start,long length,boolean partial) {}
    static Range range(String header,long size) {
        if (header==null) return new Range(0,size,false);
        try {
            if (size==0 || !header.matches("bytes=\\d*-\\d*") || header.equals("bytes=-")) throw new IllegalArgumentException();
            String[] p=header.substring(6).split("-",-1); long start=0,end=size-1;
            if (p[0].isEmpty()) { long suffix=Long.parseLong(p[1]); if(suffix<=0)throw new IllegalArgumentException(); start=Math.max(0,size-suffix); }
            else { start=Long.parseLong(p[0]); if(!p[1].isEmpty())end=Math.min(end,Long.parseLong(p[1])); }
            if(start>end || start>=size)throw new IllegalArgumentException(); return new Range(start,end-start+1,true);
        } catch(IllegalArgumentException e) { throw new IllegalArgumentException("Unsatisfiable range"); }
    }
    @GetMapping("/{id}/download") public ResponseEntity<StreamingResponseBody> download(@PathVariable("id") String id,
            @RequestHeader(value="Range",required=false) String header,
            @RequestHeader(value="If-Range",required=false) String ifRange) throws IOException {
        var info=service.info(id); Range range;
        String etag="\""+info.sha256()+"\"";
        // If-Range must match the strong ETag; otherwise return the whole current file (200).
        if (ifRange != null && !ifRange.equals(etag)) header=null;
        try { range=range(header,info.size()); }
        catch(IllegalArgumentException e) { return ResponseEntity.status(416).header(HttpHeaders.CONTENT_RANGE,"bytes */"+info.size()).build(); }
        StreamingResponseBody body=out->{try(InputStream in=service.open(id,range.start(),range.length())){LocalFileService.copyExactly(in,out,range.length());}};
        var response=ResponseEntity.status(range.partial()?206:200).contentType(MediaType.APPLICATION_OCTET_STREAM).contentLength(range.length())
            .header(HttpHeaders.ACCEPT_RANGES,"bytes").header(HttpHeaders.ETAG,etag)
            .header(HttpHeaders.CONTENT_DISPOSITION,ContentDisposition.attachment().filename(info.name(),StandardCharsets.UTF_8).build().toString());
        if(range.partial())response.header(HttpHeaders.CONTENT_RANGE,"bytes "+range.start()+"-"+(range.start()+range.length()-1)+"/"+info.size());
        return response.body(body);
    }
    @PostMapping("/batch-download") public ResponseEntity<StreamingResponseBody> zip(@RequestBody List<String> ids) throws IOException {
        if(ids==null || ids.isEmpty() || ids.size()>100)throw LocalFileService.bad("Select 1-100 files");
        List<LocalFileService.FileInfo> selected=new ArrayList<>();
        for(String id:new LinkedHashSet<>(ids))selected.add(service.info(id));
        if(selected.stream().anyMatch(f->f.size()>LocalFileService.MAX_SMALL) || selected.stream().mapToLong(LocalFileService.FileInfo::size).sum()>LocalFileService.MAX_BATCH)
            throw LocalFileService.bad("ZIP batch supports files <=2 MiB, total <=64 MiB");
        StreamingResponseBody body=out->{try(ZipOutputStream zip=new ZipOutputStream(out,StandardCharsets.UTF_8)){
            for(var file:selected){
                zip.putNextEntry(new ZipEntry(file.id()+"_"+LocalFileService.filename(file.name())));
                try(InputStream in=service.open(file.id(),0,file.size())){LocalFileService.copyExactly(in,zip,file.size());}
                zip.closeEntry();
            }
        }};
        return ResponseEntity.ok().contentType(MediaType.parseMediaType("application/zip")).header(HttpHeaders.CONTENT_DISPOSITION,"attachment; filename=files.zip").body(body);
    }
}
