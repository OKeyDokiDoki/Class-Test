package com.lifecircle.storage;

import org.junit.jupiter.api.*;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.mock.env.MockEnvironment;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.web.servlet.*;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;
import java.io.*;
import java.nio.file.*;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.*;
import java.util.zip.ZipInputStream;
import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

class FileStorageTests {
    @TempDir Path root;
    LocalFileService files; ChunkUploadService chunks; MockMvc mvc;
    @BeforeEach void setup() throws Exception {
        files=new LocalFileService(root.toString()); chunks=new ChunkUploadService(root.toString(),files);
        mvc=MockMvcBuilders.standaloneSetup(new LocalFileController(files,chunks)).setControllerAdvice(new LocalFileExceptionHandler()).build();
    }
    static String hash(byte[] bytes) throws Exception { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
    static MockMultipartFile part(byte[] bytes) { return new MockMultipartFile("file","part","application/octet-stream",bytes); }
    byte[] download(String id,String range,int expectedStatus) throws Exception {
        var request=get("/api/files/"+id+"/download"); if(range!=null)request.header("Range",range);
        MvcResult result=mvc.perform(request).andReturn();
        if(result.getRequest().isAsyncStarted())result=mvc.perform(asyncDispatch(result)).andExpect(status().is(expectedStatus)).andReturn();
        else assertEquals(expectedStatus,result.getResponse().getStatus());
        return result.getResponse().getContentAsByteArray();
    }
    @Test void readsOriginalStageOneMetadataWithoutMigration() throws Exception {
        String id=UUID.randomUUID().toString(); byte[] bytes={4,5,6};
        Properties old=new Properties(); old.setProperty("id",id); old.setProperty("name","legacy.txt"); old.setProperty("size","3");
        old.setProperty("sha256",hash(bytes)); old.setProperty("createdAt",Instant.now().toString());
        LocalFileService.saveProperties(root.resolve("metadata").resolve(id+".properties"),old);
        Files.write(root.resolve("objects").resolve(id),bytes);
        assertEquals("local",files.info(id).provider()); assertArrayEquals(bytes,download(id,null,200));
    }
    @Test void outOfOrderUploadResumesAfterRestartAndCompletesIdempotently() throws Exception {
        byte[] data=new byte[2*1024*1024+7]; new Random(42).nextBytes(data); int size=1024*1024;
        var session=chunks.init(new ChunkUploadService.Init("large.bin",data.length,size,hash(data)));
        for(int index:new int[]{2,0,0}) { byte[] slice=Arrays.copyOfRange(data,index*size,Math.min(data.length,(index+1)*size)); chunks.chunk(session.id(),index,part(slice),hash(slice)); }
        assertEquals(List.of(0,2),chunks.status(session.id()).uploaded());
        assertEquals(409,assertThrows(ResponseStatusException.class,()->chunks.complete(session.id())).getStatusCode().value());
        files=new LocalFileService(root.toString()); chunks=new ChunkUploadService(root.toString(),files);
        assertEquals(2,chunks.status(session.id()).chunkHashes().size());
        byte[] middle=Arrays.copyOfRange(data,size,2*size); chunks.chunk(session.id(),1,part(middle),hash(middle));
        var saved=chunks.complete(session.id());
        assertEquals(hash(data),saved.sha256()); assertArrayEquals(data,Files.readAllBytes(files.object(saved.id())));
        assertEquals(saved.id(),chunks.complete(session.id()).id()); assertEquals(1,files.list().size());
        assertNotNull(chunks.status(session.id()).completed()); assertFalse(Files.exists(root.resolve("uploads").resolve(session.id())));
    }
    @Test void rejectsInvalidChunkSizeIndexHashAndConflictingRetry() throws Exception {
        byte[] data=new byte[1024*1024]; var session=chunks.init(new ChunkUploadService.Init("a.bin",data.length,data.length,null));
        assertThrows(ResponseStatusException.class,()->chunks.chunk(session.id(),1,part(data),hash(data)));
        assertThrows(ResponseStatusException.class,()->chunks.chunk(session.id(),0,part(new byte[1]),hash(data)));
        assertThrows(ResponseStatusException.class,()->chunks.chunk(session.id(),0,part(data),"f".repeat(64)));
        chunks.chunk(session.id(),0,part(data),hash(data)); data[0]=1;
        assertEquals(409,assertThrows(ResponseStatusException.class,()->chunks.chunk(session.id(),0,part(data),hash(data))).getStatusCode().value());
        assertTrue(files.list().isEmpty());
    }
    @Test void finalChecksumMismatchDoesNotPublishAndSessionCanBeCancelled() throws Exception {
        byte[] data={1,2}; var session=chunks.init(new ChunkUploadService.Init("bad.bin",2,1024*1024,"f".repeat(64)));
        chunks.chunk(session.id(),0,part(data),hash(data)); assertThrows(ResponseStatusException.class,()->chunks.complete(session.id()));
        assertTrue(files.list().isEmpty()); assertEquals(List.of(0),chunks.status(session.id()).uploaded());
        chunks.cancel(session.id()); assertEquals(404,assertThrows(ResponseStatusException.class,()->chunks.status(session.id())).getStatusCode().value());
    }
    @Test void detectsCorruptedStagedChunkBeforePublishing() throws Exception {
        byte[] data={1,2}; var session=chunks.init(new ChunkUploadService.Init("bad.bin",2,1024*1024,null));
        chunks.chunk(session.id(),0,part(data),hash(data)); Files.write(root.resolve("uploads").resolve(session.id()).resolve("0.part"),new byte[]{8,9});
        assertThrows(ResponseStatusException.class,()->chunks.complete(session.id())); assertTrue(files.list().isEmpty());
    }
    @Test void supportsZeroByteFilesAndRangeDownloads() throws Exception {
        var empty=chunks.complete(chunks.init(new ChunkUploadService.Init("empty",0,1024*1024,null)).id());
        assertEquals(0,download(empty.id(),null,200).length); download(empty.id(),"bytes=0-",416);
        var file=files.upload(new MockMultipartFile("file","range.bin","application/octet-stream",new byte[]{0,1,2,3,4}));
        assertArrayEquals(new byte[]{1,2,3},download(file.id(),"bytes=1-3",206));
        assertArrayEquals(new byte[]{3,4},download(file.id(),"bytes=-2",206));
        assertArrayEquals(new byte[]{4},download(file.id(),"bytes=4-",206));
        for(String invalid:List.of("bytes=9-","bytes=3-1","bytes=0-1,3-4","bytes=-0"))download(file.id(),invalid,416);
    }
    @Test void batchReturnsPerFileErrorsAndZipRetainsDistinctSameNames() throws Exception {
        MockMultipartFile broken=new MockMultipartFile("files","broken","text/plain",new byte[]{1}) {
            @Override public InputStream getInputStream() throws IOException { throw new IOException("simulated failure"); }
        };
        var result=files.batch(new MultipartFile[]{new MockMultipartFile("files","same.txt","text/plain",new byte[]{1}),broken,
            new MockMultipartFile("files","same.txt","text/plain",new byte[]{2})});
        assertNotNull(result.get(0).file()); assertNotNull(result.get(1).error()); assertNotNull(result.get(2).file());
        String body="[\""+result.get(0).file().id()+"\",\""+result.get(2).file().id()+"\"]";
        var response=mvc.perform(post("/api/files/batch-download").contentType("application/json").content(body)).andReturn();
        byte[] zip=mvc.perform(asyncDispatch(response)).andExpect(status().isOk()).andReturn().getResponse().getContentAsByteArray();
        Set<String> names=new HashSet<>(); List<Integer> values=new ArrayList<>();
        try(ZipInputStream in=new ZipInputStream(new ByteArrayInputStream(zip))) { java.util.zip.ZipEntry entry;
            while((entry=in.getNextEntry())!=null) { assertTrue(names.add(entry.getName())); values.add(in.readAllBytes()[0]&255); } }
        assertEquals(List.of(1,2),values);
    }
    @Test void enforcesBatchAndSessionLimitsBeforeWriting() throws Exception {
        assertThrows(ResponseStatusException.class,()->files.batch(new MultipartFile[0]));
        assertThrows(ResponseStatusException.class,()->files.batch(new MultipartFile[]{new MockMultipartFile("files","big","",new byte[2*1024*1024+1])}));
        assertThrows(ResponseStatusException.class,()->chunks.init(new ChunkUploadService.Init("../escape",1,1024*1024,null)));
        assertThrows(ResponseStatusException.class,()->chunks.init(new ChunkUploadService.Init("big",ChunkUploadService.MAX_SIZE+1,1024*1024,null)));
        assertThrows(ResponseStatusException.class,()->chunks.init(new ChunkUploadService.Init("bad",1,5,null)));
        assertTrue(files.list().isEmpty());
    }
    @Test void checksumFailureReportsExactChunkAndAllowsRetry() throws Exception {
        byte[] original={1,2,3}, damaged={9,2,3};
        var session=chunks.init(new ChunkUploadService.Init("repair.bin",3,1024*1024,hash(original)));
        var result=mvc.perform(multipart("/api/files/uploads/"+session.id()+"/chunks/0")
            .file(part(damaged)).param("sha256",hash(original)).with(r->{r.setMethod("PUT");return r;}))
            .andExpect(status().is(422)).andReturn();
        var body=new com.fasterxml.jackson.databind.ObjectMapper().readTree(result.getResponse().getContentAsString());
        assertEquals("CHUNK_CHECKSUM_MISMATCH",body.get("code").asText());
        assertEquals(0,body.get("data").get("indexes").get(0).asInt());
        assertTrue(chunks.status(session.id()).uploaded().isEmpty());
        chunks.chunk(session.id(),0,part(original),hash(original));
        assertEquals(hash(original),chunks.complete(session.id()).sha256());
    }
    @Test void completionInvalidatesDamagedPartsAndRepairsOnlyMissingIndexes() throws Exception {
        int size=1024*1024; byte[] data=new byte[2*size+3];new Random(19).nextBytes(data);
        var session=chunks.init(new ChunkUploadService.Init("repair-all.bin",data.length,size,hash(data)));
        for(int i=0;i<2;i++) {byte[] slice=Arrays.copyOfRange(data,i*size,(i+1)*size);chunks.chunk(session.id(),i,part(slice),hash(slice));}
        Files.write(root.resolve("uploads").resolve(session.id()).resolve("1.part"),new byte[]{0});
        var response=mvc.perform(post("/api/files/uploads/"+session.id()+"/complete")).andExpect(status().isConflict()).andReturn();
        var body=new com.fasterxml.jackson.databind.ObjectMapper().readTree(response.getResponse().getContentAsString());
        assertEquals("CHUNK_REPAIR_REQUIRED",body.get("code").asText());
        assertEquals("[1,2]",body.get("data").get("indexes").toString());
        assertEquals(List.of(0),chunks.status(session.id()).uploaded());
        for(int i=1;i<3;i++) {byte[] slice=Arrays.copyOfRange(data,i*size,Math.min(data.length,(i+1)*size));chunks.chunk(session.id(),i,part(slice),hash(slice));}
        assertEquals(hash(data),chunks.complete(session.id()).sha256());
    }
    @Test void sameOriginalBytesCanRepairDamagedDiskChunkWithoutReplacingHealthyContent() throws Exception {
        byte[] data={1,2,3};var session=chunks.init(new ChunkUploadService.Init("repair-direct.bin",3,1024*1024,null));
        chunks.chunk(session.id(),0,part(data),hash(data));
        Files.write(root.resolve("uploads").resolve(session.id()).resolve("0.part"),new byte[]{9,2,3});
        chunks.chunk(session.id(),0,part(data),hash(data));
        assertEquals(hash(data),chunks.complete(session.id()).sha256());
    }
    @Test void ifRangeRequiresMatchingStrongEtagToAppend() throws Exception {
        byte[] data={0,1,2,3};var file=files.upload(new MockMultipartFile("file","etag.bin","",data));
        for(boolean match:List.of(true,false)) {
            var result=mvc.perform(get("/api/files/"+file.id()+"/download").header("Range","bytes=2-")
                .header("If-Range",match?"\""+file.sha256()+"\"":"\"old\"")).andReturn();
            var response=mvc.perform(asyncDispatch(result)).andExpect(status().is(match?206:200)).andReturn().getResponse();
            assertArrayEquals(match?new byte[]{2,3}:data,response.getContentAsByteArray());
        }
    }
    @Test void concurrencyBudgetRejectsExcessAndReleasesExactlyOnce() throws Exception {
        var capacity=new DownloadCapacity(1);var lease=capacity.acquire();assertNotNull(lease);
        var guarded=MockMvcBuilders.standaloneSetup(new LocalFileController(files,chunks))
            .addFilters(new DownloadAdmissionFilter(capacity)).build();
        guarded.perform(get("/api/files/"+UUID.randomUUID()+"/download")).andExpect(status().is(429))
            .andExpect(header().string("Retry-After","2"));
        lease.release(true);lease.release(false);
        assertEquals(0,capacity.snapshot().get("active"));assertEquals(1L,capacity.snapshot().get("completed"));
        assertEquals(0L,capacity.snapshot().get("failed"));assertEquals(1L,capacity.snapshot().get("rejected"));
        var next=capacity.acquire();assertNotNull(next);next.release(false);
        assertEquals(1L,capacity.snapshot().get("failed"));
    }
}
