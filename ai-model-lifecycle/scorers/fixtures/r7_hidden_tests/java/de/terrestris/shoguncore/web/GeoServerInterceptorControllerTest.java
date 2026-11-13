package de.terrestris.shoguncore.web;

import com.fasterxml.jackson.databind.ObjectMapper;
import de.terrestris.shoguncore.service.GeoServerInterceptorService;
import de.terrestris.shoguncore.util.data.ResultSet;
import de.terrestris.shoguncore.util.interceptor.InterceptorException;
import de.terrestris.shoguncore.util.model.Response;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentMatchers;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import jakarta.servlet.http.HttpServletRequest;

import java.util.Optional;

import static de.terrestris.shoguncore.web.GeoServerInterceptorController.ERROR_MESSAGE;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Test class for {@link GeoServerInterceptorController}
 */
public class GeoServerInterceptorControllerTest {

    private final String INTERCEPTOR_ENDPOINT = "/geoserver.action";

    private MockMvc mockMvc;

    @Mock(name = "geoServerInterceptorService")
    private GeoServerInterceptorService geoServerInterceptorService;

    @BeforeEach
    public void setup() {
        // Process mock annotations
        MockitoAnnotations.openMocks(this);

        GeoServerInterceptorController geoServerInterceptorController = new GeoServerInterceptorController();
        geoServerInterceptorController.setService(geoServerInterceptorService);

        // Setup Spring test in standalone mode
        this.mockMvc = MockMvcBuilders.standaloneSetup(geoServerInterceptorController).build();
    }

    @Test
    public void worksForHttpGet() throws Exception {
        final String testString = "test";
        HttpHeaders responseHeaders = new HttpHeaders();
        Response responseObject = new Response(HttpStatus.OK, responseHeaders, testString.getBytes());

        Mockito.when(geoServerInterceptorService.interceptGeoServerRequest(
            ArgumentMatchers.any(HttpServletRequest.class),
            ArgumentMatchers.any(Optional.class)
        )).thenReturn(responseObject);

        MvcResult result = mockMvc.perform(MockMvcRequestBuilders.get(INTERCEPTOR_ENDPOINT))
            .andExpect(status().isOk()).andReturn();

        assertEquals(result.getResponse().getStatus(), HttpStatus.OK.value());
        assertEquals(result.getResponse().getContentAsString(), testString);
    }

    @Test
    public void worksForHttpPost() throws Exception {
        final String testString = "test";
        HttpHeaders responseHeaders = new HttpHeaders();
        Response responseObject = new Response(HttpStatus.OK, responseHeaders, testString.getBytes());

        Mockito.when(geoServerInterceptorService.interceptGeoServerRequest(
            ArgumentMatchers.any(HttpServletRequest.class),
            ArgumentMatchers.any(Optional.class)
        )).thenReturn(responseObject);

        MvcResult result = mockMvc.perform(MockMvcRequestBuilders.post(INTERCEPTOR_ENDPOINT))
            .andExpect(status().isOk()).andReturn();

        assertEquals(result.getResponse().getStatus(), HttpStatus.OK.value());
        assertEquals(result.getResponse().getContentAsString(), testString);
    }

    @Test
    public void doesntWorkForHttpPut() throws Exception {
        final String testString = "test";
        HttpHeaders responseHeaders = new HttpHeaders();
        Response responseObject = new Response(HttpStatus.OK, responseHeaders, testString.getBytes());

        Mockito.when(geoServerInterceptorService.interceptGeoServerRequest(
            ArgumentMatchers.any(HttpServletRequest.class)
        )).thenReturn(responseObject);

        /**
         * return method not allowed
         */
        mockMvc.perform(MockMvcRequestBuilders.put(INTERCEPTOR_ENDPOINT))
            .andExpect(status().isMethodNotAllowed()).andReturn();
    }

    @Test
    public void returnsErrorObjectIfExceptionWasThrown() throws Exception {
        // the controller calls the variant with the (optional) endpoint
        Mockito.when(geoServerInterceptorService.interceptGeoServerRequest(
            ArgumentMatchers.any(HttpServletRequest.class),
            ArgumentMatchers.any()
        )).thenThrow(InterceptorException.class);

        MvcResult result = mockMvc.perform(MockMvcRequestBuilders.get(INTERCEPTOR_ENDPOINT))
            .andExpect(status().isOk()).andReturn();

        ObjectMapper objectMapper = new ObjectMapper();
        assertEquals(objectMapper.writeValueAsString(ResultSet.error(ERROR_MESSAGE+"null")), result.getResponse().getContentAsString(), "Returned body matched mocked one.");
    }

}
