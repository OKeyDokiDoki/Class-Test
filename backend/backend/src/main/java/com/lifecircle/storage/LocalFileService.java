package com.lifecircle.storage;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.*;
import java.time.Instant;
import java.util.*;

/** Stage 1: persist file bytes and metadata locally, without changing business tables. */
@Service
public class LocalFileService {
    public record FileInfo(String id, String name, long size, String sha256, Instant createdAt) {}
    private static final long MAX_SIZE = 5L * 1024 * 1024;
    private final Path root;

    public LocalFileService(@Value("${storage.local.root:./data/files}") String directory) throws IOException {
        root = Path.of(directory).toAbsolutePath().normalize();
        Files.createDirectories(root.resolve("objects"));
        Files.createDirectories(root.resolve("metadata"));
    }

    private static void validateId(String id) {
        try {
            if (!UUID.fromString(id).toString().equals(id)) throw new IllegalArgumentException();
        } catch (Exception e) { throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Invalid file ID"); }
    }
    private Path metadata(String id) { validateId(id); return root.resolve("metadata").resolve(id + ".properties"); }

    public FileInfo upload(MultipartFile file) throws IOException {
        String filename = file.getOriginalFilename();
        if (filename == null || filename.isBlank() || filename.length() > 180 || filename.equals(".")
            || filename.equals("..") || filename.contains("/") || filename.contains("\\")
            || filename.chars().anyMatch(c -> c < 32))
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Invalid filename");
        if (file.getSize() > MAX_SIZE)
            throw new ResponseStatusException(HttpStatus.PAYLOAD_TOO_LARGE, "Stage 1 supports files up to 5 MiB");
        String id = UUID.randomUUID().toString();
        Path temp = Files.createTempFile(root, "upload-", ".tmp");
        Path metaTemp = Files.createTempFile(root.resolve("metadata"), "metadata-", ".tmp");
        Path object = root.resolve("objects").resolve(id);
        boolean committed = false;
        try {
            MessageDigest digest;
            try { digest = MessageDigest.getInstance("SHA-256"); }
            catch (NoSuchAlgorithmException e) { throw new IllegalStateException(e); }
            long size = 0;
            try (InputStream in = file.getInputStream(); OutputStream out = Files.newOutputStream(temp)) {
                byte[] buffer = new byte[64 * 1024]; int n;
                while ((n = in.read(buffer)) != -1) {
                    size += n;
                    if (size > MAX_SIZE) throw new ResponseStatusException(HttpStatus.PAYLOAD_TOO_LARGE, "File exceeds 5 MiB");
                    digest.update(buffer, 0, n); out.write(buffer, 0, n);
                }
            }
            FileInfo info = new FileInfo(id, filename, size, HexFormat.of().formatHex(digest.digest()), Instant.now());
            Properties properties = new Properties();
            properties.setProperty("id", id); properties.setProperty("name", filename);
            properties.setProperty("size", Long.toString(size)); properties.setProperty("sha256", info.sha256());
            properties.setProperty("createdAt", info.createdAt().toString());
            try (Writer writer = Files.newBufferedWriter(metaTemp, StandardCharsets.UTF_8)) {
                properties.store(writer, "Local file metadata");
            }
            move(temp, object);
            move(metaTemp, metadata(id));
            committed = true;
            return info;
        } finally {
            Files.deleteIfExists(temp); Files.deleteIfExists(metaTemp);
            if (!committed) Files.deleteIfExists(object);
        }
    }

    private static void move(Path source, Path target) throws IOException {
        try { Files.move(source, target, StandardCopyOption.ATOMIC_MOVE); }
        catch (AtomicMoveNotSupportedException e) { Files.move(source, target); }
    }
    public FileInfo info(String id) throws IOException {
        Path path = metadata(id);
        if (!Files.exists(path)) throw new ResponseStatusException(HttpStatus.NOT_FOUND, "File not found");
        Properties properties = new Properties();
        try (Reader reader = Files.newBufferedReader(path, StandardCharsets.UTF_8)) { properties.load(reader); }
        return new FileInfo(id, properties.getProperty("name"), Long.parseLong(properties.getProperty("size")),
            properties.getProperty("sha256"), Instant.parse(properties.getProperty("createdAt")));
    }
    public Path object(String id) throws IOException {
        info(id);
        Path path = root.resolve("objects").resolve(id);
        if (!Files.isRegularFile(path)) throw new ResponseStatusException(HttpStatus.NOT_FOUND, "File content missing");
        return path;
    }
    public List<FileInfo> list() throws IOException {
        List<FileInfo> result = new ArrayList<>();
        try (var paths = Files.list(root.resolve("metadata"))) {
            for (Path path : paths.filter(p -> p.getFileName().toString().endsWith(".properties")).toList()) {
                String filename = path.getFileName().toString();
                result.add(info(filename.substring(0, filename.length() - ".properties".length())));
            }
        }
        result.sort(Comparator.comparing(FileInfo::createdAt).reversed()); return result;
    }
}
