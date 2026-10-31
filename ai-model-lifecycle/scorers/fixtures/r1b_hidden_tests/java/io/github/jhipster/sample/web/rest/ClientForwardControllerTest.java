package io.github.jhipster.sample.web.rest;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.forwardedUrl;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.Properties;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.config.YamlPropertiesFactoryBean;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.ResultActions;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * Unit tests for the {@link ClientForwardController} REST controller.
 */
class ClientForwardControllerTest {

    private MockMvc restMockMvc;

    @BeforeEach
    public void setup() {
        ClientForwardController clientForwardController = new ClientForwardController();
        var builder = MockMvcBuilders.standaloneSetup(clientForwardController, new TestController());
        // A standalone MockMvc does not read application.yml. Match the app's own
        // spring.mvc.pathmatch.matching-strategy, so the test checks the forwarding
        // behavior, not which of Boot 3's two supported matchers the migration kept.
        if (usesAntPathMatcher()) {
            builder.setPatternParser(null);
        }
        this.restMockMvc = builder.build();
    }

    private static boolean usesAntPathMatcher() {
        YamlPropertiesFactoryBean yaml = new YamlPropertiesFactoryBean();
        yaml.setResources(new FileSystemResource("src/main/resources/config/application.yml"));
        Properties props = yaml.getObject();
        String strategy = props == null ? null : props.getProperty("spring.mvc.pathmatch.matching-strategy");
        return strategy != null && strategy.trim().toLowerCase().replace('-', '_').equals("ant_path_matcher");
    }

    @Test
    void getBackendEndpoint() throws Exception {
        restMockMvc
            .perform(get("/test"))
            .andExpect(status().isOk())
            .andExpect(content().contentTypeCompatibleWith(MediaType.TEXT_PLAIN_VALUE))
            .andExpect(content().string("test"));
    }

    @Test
    void getClientEndpoint() throws Exception {
        ResultActions perform = restMockMvc.perform(get("/non-existant-mapping"));
        perform.andExpect(status().isOk()).andExpect(forwardedUrl("/"));
    }

    @Test
    void getNestedClientEndpoint() throws Exception {
        restMockMvc.perform(get("/admin/user-management")).andExpect(status().isOk()).andExpect(forwardedUrl("/"));
    }

    @Test
    void getUnmappedDottedEndpoint() throws Exception {
        restMockMvc.perform(get("/foo.js")).andExpect(status().isNotFound());
    }

    @Test
    void getUnmappedNestedDottedEndpoint() throws Exception {
        restMockMvc.perform(get("/foo/bar.js")).andExpect(status().isNotFound());
    }

    @RestController
    public static class TestController {

        @RequestMapping(value = "/test")
        public String test() {
            return "test";
        }
    }
}
