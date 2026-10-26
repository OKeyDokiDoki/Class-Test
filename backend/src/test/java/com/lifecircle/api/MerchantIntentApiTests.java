package com.lifecircle.api;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class MerchantIntentApiTests {
    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void createsAndReadsMerchantIntent() throws Exception {
        String response = mockMvc.perform(post("/api/merchant/intents")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {
                      "merchantName": "邻里便利店",
                      "businessType": "便利店",
                      "contact": "13800000000"
                    }
                    """))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.data.status").value("submitted"))
            .andExpect(jsonPath("$.data.id").isNumber())
            .andReturn()
            .getResponse()
            .getContentAsString();

        JsonNode created = objectMapper.readTree(response);
        long id = created.path("data").path("id").asLong();

        String listResponse = mockMvc.perform(get("/api/merchant/intents"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.data[0].merchantName").value("邻里便利店"))
            .andReturn()
            .getResponse()
            .getContentAsString();

        JsonNode intents = objectMapper.readTree(listResponse).path("data");
        assertThat(intents)
            .anySatisfy(intent -> assertThat(intent.path("id").asLong()).isEqualTo(id));
    }
}
