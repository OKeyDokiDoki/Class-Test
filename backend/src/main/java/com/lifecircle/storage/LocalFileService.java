package com.lifecircle.storage;

import org.springframework.beans.factory.annotation.Autowired;
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

/** First-stage APIs and .properties metadata remain compatible after this upgrade. */
@Service
public class LocalFileService {
    public record FileInfo(String id, String name, long size, String sha256, Instant createdAt, String provider) {}
    public record BatchItem(String name, FileInfo file, String error) {}
    static final long MAX_SINGLE = 5L * 1024 * 1024, MAX_BATCH = 64L * 1024 * 1024, MAX_SMALL = 2L * 1024 * 1024;
    private final Path root;
    private final ObjectStore store;
    public LocalFileService(String directory) throws IOException { this(directory, new ObjectStore(directory)); }
    @Autowired public LocalFileService(@Value("${storage.local.root:./data/files}") String directory, ObjectStore store) throws IOException {
        root = Path.of(directory).toAbsolutePath().normalize(); this.store = store;
        Files.createDirectories(root.resolve("metadata"));
    }
    static String validateId(String id) {
        try { if (!UUID.fromString(id).toString().equals(id)) throw new IllegalArgumentException(); return id; }
        catch (Exception e) { throw bad("Invalid file/upload ID"); }
    }
    static ResponseStatusException bad(String message) { return new ResponseStatusException(HttpStatus.BAD_REQUEST, message); }
    static String filename(String name) {
        if (name == null || name.isBlank() || name.length() > 180 || name.equals(".") || name.equals("..")
            || name.contains("/") || name.contains("\\") || name.chars().anyMatch(c -> c < 32)) throw bad("Invalid filename");
        return name;
    }
    private Path metadata(String id) { return root.resolve("metadata").resolve(validateId(id) + ".properties"); }
    static void move(Path source, Path target) throws IOException {
        try { Files.move(source, target, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING); }
        catch (AtomicMoveNotSupportedException e) { Files.move(source, target, StandardCopyOption.REPLACE_EXISTING); }
    }
    static void saveProperties(Path target, Properties value) throws IOException {
        Path temp = Files.createTempFile(target.getParent(), "metadata-", ".tmp");
        try {
            try (Writer writer = Files.newBufferedWriter(temp, StandardCharsets.UTF_8)) { value.store(writer, "File storage metadata"); }
            move(temp, target);
        } finally { Files.deleteIfExists(temp); }
    }
    static Properties loadProperties(Path path) throws IOException {
        Properties properties = new Properties();
        try (Reader reader = Files.newBufferedReader(path, StandardCharsets.UTF_8)) { properties.load(reader); }
        return properties;
    }
    static MessageDigest digest() {
        try { return MessageDigest.getInstance("SHA-256"); }
        catch (NoSuchAlgorithmException e) { throw new IllegalStateException(e); }
    }
    static String hash(Path path) throws IOException {
        MessageDigest digest = digest();
        try (InputStream in = new DigestInputStream(Files.newInputStream(path), digest)) { in.transferTo(OutputStream.nullOutputStream()); }
        return HexFormat.of().formatHex(digest.digest());
    }
    public String mode() { return store.mode(); }
    public FileInfo upload(MultipartFile file) throws IOException {
        filename(file.getOriginalFilename());
        if (file.getSize() > MAX_SINGLE) throw new ResponseStatusException(HttpStatus.PAYLOAD_TOO_LARGE, "Single upload exceeds 5 MiB; use chunks");
        Path temp = Files.createTempFile(root, "upload-", ".tmp");
        try {
            try (InputStream in = file.getInputStream(); OutputStream out = Files.newOutputStream(temp)) { copyLimited(in, out, MAX_SINGLE); }
            return publish(UUID.randomUUID().toString(), file.getOriginalFilename(), temp, hash(temp));
        } finally { Files.deleteIfExists(temp); }
    }
    /** Object first, metadata last: the list only exposes committed files. */
    FileInfo publish(String id, String name, Path source, String sha256) throws IOException {
        validateId(id); filename(name);
        ObjectStore.Location where = store.write(id, source);
        try {
            FileInfo info = new FileInfo(id, name, Files.size(source), sha256, Instant.now(), where.provider());
            Properties p = new Properties();
            p.setProperty("id", id); p.setProperty("name", name); p.setProperty("size", Long.toString(info.size()));
            p.setProperty("sha256", sha256); p.setProperty("createdAt", info.createdAt().toString());
            p.setProperty("provider", where.provider()); p.setProperty("key", where.key());
            p.setProperty("endpoint", where.endpoint()); p.setProperty("bucket", where.bucket()); p.setProperty("region", where.region());
            saveProperties(metadata(id), p); return info;
        } catch (IOException | RuntimeException e) {
            try { store.delete(where); } catch (IOException cleanup) { e.addSuppressed(cleanup); }
            throw e;
        }
    }
    public boolean exists(String id) { return Files.exists(metadata(id)); }
    private Properties properties(String id) throws IOException {
        Path path = metadata(id);
        if (!Files.exists(path)) throw new ResponseStatusException(HttpStatus.NOT_FOUND, "File not found");
        return loadProperties(path);
    }
    public FileInfo info(String id) throws IOException {
        Properties p = properties(id);
        return new FileInfo(id, p.getProperty("name"), Long.parseLong(p.getProperty("size")), p.getProperty("sha256"),
            Instant.parse(p.getProperty("createdAt")), p.getProperty("provider", "local"));
    }
    public InputStream open(String id, long offset, long length) throws IOException {
        Properties p = properties(id);
        return store.open(new ObjectStore.Location(p.getProperty("provider", "local"), p.getProperty("key", id),
            p.getProperty("endpoint", ""), p.getProperty("bucket", ""), p.getProperty("region", "")), offset, length);
    }
    /** Kept for first-stage callers; cloud files must use open(). */
    public Path object(String id) throws IOException {
        if (!info(id).provider().equals("local")) throw bad("Use the download API for cloud files");
        Path path = root.resolve("objects").resolve(id);
        if (!Files.isRegularFile(path)) throw new ResponseStatusException(HttpStatus.NOT_FOUND, "File content missing");
        return path;
    }
    public List<FileInfo> list() throws IOException {
        List<FileInfo> result = new ArrayList<>();
        try (var paths = Files.list(root.resolve("metadata"))) {
            for (Path path : paths.filter(p -> p.getFileName().toString().endsWith(".properties")).toList()) {
                String name = path.getFileName().toString(); result.add(info(name.substring(0, name.length() - 11)));
            }
        }
        result.sort(Comparator.comparing(FileInfo::createdAt).reversed()); return result;
    }
    public List<BatchItem> batch(MultipartFile[] files) throws IOException {
        if (files == null || files.length == 0 || files.length > 100) throw bad("Select 1-100 files");
        long total = 0;
        for (MultipartFile file : files) {
            filename(file.getOriginalFilename());
            if (file.getSize() > MAX_SMALL) throw bad("Each batch file must be <=2 MiB");
            total += file.getSize();
        }
        if (total > MAX_BATCH) throw bad("Batch total must be <=64 MiB");
        List<BatchItem> result = new ArrayList<>();
        for (MultipartFile file : files) {
            try { result.add(new BatchItem(file.getOriginalFilename(), upload(file), null)); }
            catch (IOException e) { result.add(new BatchItem(file.getOriginalFilename(), null, "Storage write failed; retry this file")); }
        }
        return result;
    }
    static void copyLimited(InputStream in, OutputStream out, long limit) throws IOException {
        byte[] buffer = new byte[64 * 1024]; long total = 0; int n;
        while ((n = in.read(buffer)) != -1) {
            total += n;
            if (total > limit) throw new ResponseStatusException(HttpStatus.PAYLOAD_TOO_LARGE, "Upload exceeds size limit");
            out.write(buffer, 0, n);
        }
    }
    static void copyExactly(InputStream in, OutputStream out, long length) throws IOException {
        byte[] buffer = new byte[64 * 1024]; long left = length;
        while (left > 0) {
            int n = in.read(buffer, 0, (int)Math.min(buffer.length, left));
            if (n < 0) throw new EOFException("Stored content is shorter than metadata");
            out.write(buffer, 0, n); left -= n;
        }
    }
}
