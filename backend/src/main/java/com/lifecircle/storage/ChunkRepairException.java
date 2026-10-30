package com.lifecircle.storage;

import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;
import java.util.List;

/** Machine-readable repair instructions: retransmit only these zero-based indexes. */
public class ChunkRepairException extends ResponseStatusException {
    private final String code;
    private final List<Integer> indexes;

    public ChunkRepairException(HttpStatus status, String code, String message, List<Integer> indexes) {
        super(status, message);
        this.code = code;
        this.indexes = List.copyOf(indexes);
    }
    public String code() { return code; }
    public List<Integer> indexes() { return indexes; }
}
