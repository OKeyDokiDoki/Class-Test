package com.lifecircle.storage;

import com.lifecircle.common.result.Result;
import org.springframework.core.io.*;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;

@RestController
@RequestMapping("/api/files")
public class LocalFileController {
    private final LocalFileService service;
    public LocalFileController(LocalFileService service) { this.service = service; }

    @PostMapping("/upload")
    public Result<LocalFileService.FileInfo> upload(@RequestParam("file") MultipartFile file) throws IOException {
        return Result.ok(service.upload(file));
    }
    @GetMapping
    public Result<List<LocalFileService.FileInfo>> list() throws IOException { return Result.ok(service.list()); }

    @GetMapping("/{id}/download")
    public ResponseEntity<Resource> download(@PathVariable("id") String id) throws IOException {
        LocalFileService.FileInfo info = service.info(id);
        Resource resource = new FileSystemResource(service.object(id));
        return ResponseEntity.ok().contentType(MediaType.APPLICATION_OCTET_STREAM).contentLength(info.size())
            .header(HttpHeaders.CONTENT_DISPOSITION, ContentDisposition.attachment()
                .filename(info.name(), StandardCharsets.UTF_8).build().toString())
            .header(HttpHeaders.ETAG, "\"" + info.sha256() + "\"").body(resource);
    }
}
