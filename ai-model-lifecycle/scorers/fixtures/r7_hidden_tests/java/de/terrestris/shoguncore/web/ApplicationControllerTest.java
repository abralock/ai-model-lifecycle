package de.terrestris.shoguncore.web;

import static org.hamcrest.Matchers.hasSize;
import static org.hamcrest.Matchers.is;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoMoreInteractions;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.Arrays;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.http.converter.json.MappingJackson2HttpMessageConverter;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import de.terrestris.shoguncore.dao.ApplicationDao;
import de.terrestris.shoguncore.model.Application;
import de.terrestris.shoguncore.service.ApplicationService;
import de.terrestris.shoguncore.util.json.ShogunCoreJsonObjectMapper;

/**
 * @author Nils Bühner
 */
public class ApplicationControllerTest {

    private MockMvc mockMvc;

    @Mock
    private ApplicationService<Application, ApplicationDao<Application>> applicationServiceMock;

    /**
     * The controller to test
     */
    private ApplicationController<Application, ApplicationDao<Application>, ApplicationService<Application, ApplicationDao<Application>>> applicationController;

    @BeforeEach
    public void setUp() {

        // Process mock annotations
        MockitoAnnotations.openMocks(this);

        // init the controller to test. this is necessary as InjectMocks
        // annotation will not work with the constructors of the controllers
        // (entityClass). see https://goo.gl/jLbMZe
        applicationController = new ApplicationController<Application, ApplicationDao<Application>, ApplicationService<Application, ApplicationDao<Application>>>();
        applicationController.setService(applicationServiceMock);

        // Setup Spring test in standalone mode, with JSON written the way a
        // SHOGun webapp writes it (its servlet context configures the Jackson
        // converter with ShogunCoreJsonObjectMapper). Spring 6's default
        // converter no longer registers Joda-Time on its own, so a migration
        // may rely on the project's mapper instead of annotating the entities.
        this.mockMvc = MockMvcBuilders.standaloneSetup(applicationController)
            .setMessageConverters(new MappingJackson2HttpMessageConverter(new ShogunCoreJsonObjectMapper()))
            .build();
    }

    @Test
    public void findAllApplications_shouldReturnAllApplicationEntries()
        throws Exception {

        String firstAppName = "Application 0";
        String secondAppName = "Application 1";

        String firstAppDesc = "Description of Application 0";
        String secondAppDesc = "Description of Application 1";

        Application first = new Application(firstAppName, firstAppDesc);
        Application second = new Application(secondAppName, secondAppDesc);

        when(applicationServiceMock.findAll()).thenReturn(
            Arrays.asList(first, second));

        // Perform and test the GET-Request
        mockMvc.perform(get("/application/findAll.action"))
            .andExpect(status().isOk())
            .andExpect(
                content().contentType("application/json;charset=UTF-8"))
            .andExpect(jsonPath("$", hasSize(2)))
            .andExpect(jsonPath("$[0].name", is(firstAppName)))
            .andExpect(jsonPath("$[0].description", is(firstAppDesc)))
            .andExpect(jsonPath("$[1].name", is(secondAppName)))
            .andExpect(jsonPath("$[1].description", is(secondAppDesc)));

        verify(applicationServiceMock, times(1)).findAll();
        verifyNoMoreInteractions(applicationServiceMock);
    }
}
