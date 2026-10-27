package com.lifecircle.storage;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;

@Service
public class ChunkUploadService {
    public record Init(String name, long size, int chunkSize, String sha256) {}
    public record Session(String id, String name, long size, int chunkSize, int totalChunks, String sha256, Instant createdAt) {}
    public record Status(Session session, List<Integer> uploaded, Map<Integer,String> chunkHashes, LocalFileService.FileInfo completed) {}
    public static final long MAX_SIZE = 20L * 1024 * 1024 * 1024;
    private final Path uploads;
    private final LocalFileService files;
    // One process owns the storage root; stripes bound lock memory even for many upload IDs.
    private final Object[] locks = new Object[64];
    public ChunkUploadService(@Value("${storage.local.root:./data/files}") String directory, LocalFileService files) throws IOException {
        uploads = Path.of(directory).toAbsolutePath().normalize().resolve("uploads"); this.files = files;
        Files.createDirectories(uploads); Arrays.setAll(locks, i -> new Object());
    }
    private Object lock(String id) { return locks[(LocalFileService.validateId(id).hashCode() & Integer.MAX_VALUE) % locks.length]; }
    private Path dir(String id) { return uploads.resolve(LocalFileService.validateId(id)); }
    public Session init(Init request) throws IOException {
        LocalFileService.filename(request.name());
        if (request.size() < 0 || request.size() > MAX_SIZE) throw LocalFileService.bad("File size must be 0-20 GiB");
        if (request.chunkSize() < 1024*1024 || request.chunkSize() > 8*1024*1024)
            throw LocalFileService.bad("Chunk size must be 1-8 MiB");
        if (request.sha256() != null && !request.sha256().matches("(?i)[0-9a-f]{64}"))
            throw LocalFileService.bad("SHA-256 must contain 64 hexadecimal characters");
        String id = UUID.randomUUID().toString();
        Session s = new Session(id, request.name(), request.size(), request.chunkSize(),
            (int)((request.size() + request.chunkSize()-1)/request.chunkSize()), request.sha256(), Instant.now());
        Properties p = new Properties(); p.setProperty("id", id); p.setProperty("name", s.name());
        p.setProperty("size", Long.toString(s.size())); p.setProperty("chunkSize", Integer.toString(s.chunkSize()));
        p.setProperty("sha256", s.sha256() == null ? "" : s.sha256()); p.setProperty("createdAt", s.createdAt().toString());
        Files.createDirectory(dir(id)); LocalFileService.saveProperties(dir(id).resolve("session.properties"), p); return s;
    }
    private Session session(String id) throws IOException {
        Path path = dir(id).resolve("session.properties");
        if (!Files.exists(path)) throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Upload session not found");
        Properties p = LocalFileService.loadProperties(path);
        long size = Long.parseLong(p.getProperty("size")); int chunkSize = Integer.parseInt(p.getProperty("chunkSize"));
        String hash = p.getProperty("sha256", "");
        return new Session(id, p.getProperty("name"), size, chunkSize, (int)((size+chunkSize-1)/chunkSize),
            hash.isEmpty() ? null : hash, Instant.parse(p.getProperty("createdAt")));
    }
    public Status status(String id) throws IOException {
        synchronized (lock(id)) {
            if (files.exists(id)) return new Status(null, List.of(), Map.of(), files.info(id));
            Session s = session(id); List<Integer> received = new ArrayList<>(); Map<Integer,String> hashes = new LinkedHashMap<>();
            for (int i=0;i<s.totalChunks();i++) {
                Path part = dir(id).resolve(i+".part"), hash = dir(id).resolve(i+".sha256");
                if (Files.exists(part) && Files.exists(hash)) { received.add(i); hashes.put(i, Files.readString(hash).trim()); }
            }
            return new Status(s, received, hashes, null);
        }
    }
    public void chunk(String id, int index, MultipartFile file, String expectedHash) throws IOException {
        synchronized (lock(id)) {
            if (files.exists(id)) throw new ResponseStatusException(HttpStatus.CONFLICT, "Upload already completed");
            Session s = session(id);
            if (index<0 || index>=s.totalChunks()) throw LocalFileService.bad("Chunk index out of bounds");
            if (expectedHash == null || !expectedHash.matches("(?i)[0-9a-f]{64}"))
                throw LocalFileService.bad("Each chunk requires a SHA-256 checksum");
            long size = Math.min(s.chunkSize(), s.size()-(long)index*s.chunkSize());
            if (file.getSize() != size) throw LocalFileService.bad("Chunk size mismatch");
            Path temp = Files.createTempFile(dir(id), "chunk-", ".tmp");
            try {
                try (InputStream in = file.getInputStream(); OutputStream out = Files.newOutputStream(temp)) {
                    LocalFileService.copyLimited(in, out, size);
                }
                if (Files.size(temp) != size) throw LocalFileService.bad("Incomplete chunk");
                String hash = LocalFileService.hash(temp);
                if (!hash.equalsIgnoreCase(expectedHash)) throw LocalFileService.bad("Chunk SHA-256 mismatch");
                Path part = dir(id).resolve(index+".part"), hashFile = dir(id).resolve(index+".sha256");
                if (Files.exists(part)) {
                    if (!hash.equals(LocalFileService.hash(part)))
                        throw new ResponseStatusException(HttpStatus.CONFLICT, "Chunk retry has different bytes");
                } else { LocalFileService.move(temp, part); }
                // Publish hash after bytes; an interrupted write is safe to retry.
                Path hashTemp = Files.createTempFile(dir(id), "checksum-", ".tmp");
                try { Files.writeString(hashTemp, hash, StandardCharsets.US_ASCII); LocalFileService.move(hashTemp, hashFile); }
                finally { Files.deleteIfExists(hashTemp); }
            } finally { Files.deleteIfExists(temp); }
        }
    }
    public LocalFileService.FileInfo complete(String id) throws IOException {
        synchronized (lock(id)) {
            if (files.exists(id)) return files.info(id); // idempotent after a lost response or restart
            Session s = session(id);
            for (int i=0;i<s.totalChunks();i++) {
                if (!Files.exists(dir(id).resolve(i+".part")) || !Files.exists(dir(id).resolve(i+".sha256")))
                    throw new ResponseStatusException(HttpStatus.CONFLICT, "Missing chunk " + i);
            }
            Path assembled = dir(id).resolve("assembled.tmp");
            var digest = LocalFileService.digest();
            try {
                try (OutputStream out = new java.security.DigestOutputStream(Files.newOutputStream(assembled), digest)) {
                    for (int i=0;i<s.totalChunks();i++) {
                        Path part = dir(id).resolve(i+".part");
                        long expectedSize = Math.min(s.chunkSize(), s.size()-(long)i*s.chunkSize());
                        if (Files.size(part) != expectedSize || !LocalFileService.hash(part).equals(Files.readString(dir(id).resolve(i+".sha256")).trim()))
                            throw LocalFileService.bad("Stored chunk is corrupt: " + i);
                        try (InputStream in = Files.newInputStream(part)) { LocalFileService.copyExactly(in,out,expectedSize); }
                    }
                }
                String hash = HexFormat.of().formatHex(digest.digest());
                if (Files.size(assembled) != s.size()) throw LocalFileService.bad("Final file size mismatch");
                if (s.sha256()!=null && !hash.equalsIgnoreCase(s.sha256())) throw LocalFileService.bad("Final SHA-256 mismatch");
                var result = files.publish(id,s.name(),assembled,hash);
                try { clean(dir(id)); } catch (IOException ignored) { /* metadata committed: cleanup can be retried */ }
                return result;
            } finally { Files.deleteIfExists(assembled); }
        }
    }
    public void cancel(String id) throws IOException {
        synchronized (lock(id)) {
            if (files.exists(id)) throw new ResponseStatusException(HttpStatus.CONFLICT, "Upload already completed");
            session(id); clean(dir(id));
        }
    }
    private static void clean(Path directory) throws IOException {
        try (var walk = Files.walk(directory)) {
            for (Path path : walk.sorted(Comparator.reverseOrder()).toList()) Files.deleteIfExists(path);
        }
    }
}
