package de.terrestris.shoguncore.web;

import de.terrestris.shoguncore.service.ModuleService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;

/**
 * Test class for {@link ModuleController}
 *
 * @author Andre Henn
 */
public class ModuleControllerTest {

    private MockMvc mockMvc;

    /**
     * The controller to test
     */
    private ModuleController moduleController;

    @Mock(name="moduleService")
    private ModuleService moduleService;

    @BeforeEach
    public void setUp() {
        // Process mock annotations
        MockitoAnnotations.openMocks(this);

        this.moduleController = new ModuleController();
        this.moduleController.setService(moduleService);

        // Setup Spring test in standalone mode
        this.mockMvc = MockMvcBuilders.standaloneSetup(moduleController).build();
    }

    @Test
    public void findAllRequestMappings() throws Exception {
        // Perform and test the GET-Request
        mockMvc.perform(get("/module"));
    }
}
