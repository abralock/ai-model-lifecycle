package de.terrestris.shoguncore.web;

import de.terrestris.shoguncore.service.WpsPluginService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;

/**
 * Test class for {@link WpsPluginController}
 *
 * @author Andre Henn
 */
public class WpsPluginControllerTest {

    private MockMvc mockMvc;

    /**
     * The controller to test
     */
    private WpsPluginController wpsPluginController;

    @Mock(name="wpsPluginService")
    private WpsPluginService wpsPluginService;

    @BeforeEach
    public void setUp() {
        // Process mock annotations
        MockitoAnnotations.openMocks(this);

        this.wpsPluginController = new WpsPluginController();
        this.wpsPluginController.setService(wpsPluginService);

        // Setup Spring test in standalone mode
        this.mockMvc = MockMvcBuilders.standaloneSetup(wpsPluginController).build();
    }

    @Test
    public void findAllRequestMappings() throws Exception {
        // Perform and test the GET-Request
        mockMvc.perform(get("/wpsplugins"));
    }

}
