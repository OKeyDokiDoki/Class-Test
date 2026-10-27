package com.lifecircle.storage;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.env.Environment;
import org.springframework.stereotype.Component;
import java.io.*;
import java.nio.file.*;
/** Local disk adapter for the large-file release; cloud adapters follow separately. */
@Component
public class ObjectStore {
 public record Location(String provider,String key,String endpoint,String bucket,String region) {}
 private final Path objects;
 @Autowired public ObjectStore(Environment env) throws IOException { this(env.getProperty("storage.local.root","./data/files")); }
 ObjectStore(String root) throws IOException { objects=Path.of(root).toAbsolutePath().normalize().resolve("objects");Files.createDirectories(objects); }
 public String mode(){return "local";}
 private Path path(String key){LocalFileService.validateId(key);return objects.resolve(key);}
 public Location write(String key,Path source) throws IOException {
  Path temporary=Files.createTempFile(objects,"object-",".tmp");
  try{Files.copy(source,temporary,StandardCopyOption.REPLACE_EXISTING);LocalFileService.move(temporary,path(key));}
  finally{Files.deleteIfExists(temporary);}
  return new Location("local",key,"","","");
 }
 public InputStream open(Location location,long offset,long length) throws IOException {
  if(!location.provider().equals("local"))throw new IOException("Cloud storage is not enabled in the large-file release");
  if(length==0)return InputStream.nullInputStream();
  InputStream in=Files.newInputStream(path(location.key()));try{in.skipNBytes(offset);}catch(Exception e){in.close();throw e;}return in;
 }
 public void delete(Location location)throws IOException{Files.deleteIfExists(path(location.key()));}
}
