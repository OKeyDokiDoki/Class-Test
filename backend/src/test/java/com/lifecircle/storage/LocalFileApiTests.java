package com.lifecircle.storage;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.server.ResponseStatusException;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

class LocalFileApiTests {
    @TempDir Path directory;
    @Test void persistsBytesAndMetadataAcrossServiceRestart() throws Exception {
        var first = new LocalFileService(directory.toString());
        byte[] data = "file storage demo".getBytes(StandardCharsets.UTF_8);
        var saved = first.upload(new MockMultipartFile("file", "demo.txt", "text/plain", data));
        var restarted = new LocalFileService(directory.toString());
        assertEquals(1, restarted.list().size());
        assertEquals("demo.txt", restarted.info(saved.id()).name());
        assertArrayEquals(data, Files.readAllBytes(restarted.object(saved.id())));
        assertEquals(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(data)), saved.sha256());
    }
    @Test void sameNamesDoNotOverwrite() throws Exception {
        var service = new LocalFileService(directory.toString());
        var first = service.upload(new MockMultipartFile("file", "same.txt", "text/plain", new byte[]{1}));
        var second = service.upload(new MockMultipartFile("file", "same.txt", "text/plain", new byte[]{2}));
        assertNotEquals(first.id(), second.id());
        assertArrayEquals(new byte[]{1}, Files.readAllBytes(service.object(first.id())));
        assertArrayEquals(new byte[]{2}, Files.readAllBytes(service.object(second.id())));
    }
    @Test void rejectsTraversalAndOversizedFiles() throws Exception {
        var service = new LocalFileService(directory.toString());
        var invalid = assertThrows(ResponseStatusException.class,
            () -> service.upload(new MockMultipartFile("file", "../outside.txt", "text/plain", new byte[]{1})));
        assertEquals(400, invalid.getStatusCode().value());
        var large = assertThrows(ResponseStatusException.class,
            () -> service.upload(new MockMultipartFile("file", "large.bin", "application/octet-stream", new byte[5*1024*1024+1])));
        assertEquals(413, large.getStatusCode().value());
        assertTrue(service.list().isEmpty());
    }
    @Test void uploadListAndDownloadEndpointsWork() throws Exception {
        var service = new LocalFileService(directory.toString());
        var mvc = MockMvcBuilders.standaloneSetup(new LocalFileController(service, new ChunkUploadService(directory.toString(), service)))
            .setControllerAdvice(new LocalFileExceptionHandler()).build();
        byte[] data = new byte[]{1,2,3,4};
        mvc.perform(multipart("/api/files/upload").file(new MockMultipartFile("file", "api.bin", "application/octet-stream", data)))
            .andExpect(status().isOk());
        mvc.perform(get("/api/files")).andExpect(status().isOk());
        var download = mvc.perform(get("/api/files/"+service.list().get(0).id()+"/download")).andReturn();
        mvc.perform(asyncDispatch(download)).andExpect(status().isOk()).andExpect(content().bytes(data));
        mvc.perform(get("/api/files/"+java.util.UUID.randomUUID()+"/download"))
            .andExpect(status().isNotFound());
    }
}
