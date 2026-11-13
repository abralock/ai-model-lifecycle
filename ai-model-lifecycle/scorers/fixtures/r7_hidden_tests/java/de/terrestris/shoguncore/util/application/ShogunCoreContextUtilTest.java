package de.terrestris.shoguncore.util.application;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;

import java.net.URI;
import java.net.URISyntaxException;
import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

public class ShogunCoreContextUtilTest {

    /**
     * The mockup request
     */
    private MockHttpServletRequest request;

    /**
     *
     */
    @BeforeEach
    public void setUp() {
        request = new MockHttpServletRequest();
    }

    /**
     *
     */
    @AfterEach
    public void clean() {
        request.close();
    }

    @Test
    public void getApplicationURIFromRequest_returnsAppURIonly() throws URISyntaxException {

        String scheme = "http";
        String host = "localhost";
        int port = 8080;
        String path = "/webapp";

        Map<String, String> params = new HashMap<String, String>();
        params.put("key1", "val1");
        params.put("key2", "val2");

        // mock the request
        request.setScheme(scheme);
        request.setServerName(host);
        request.setServerPort(port);
        request.setContextPath(path);
        request.setParameters(params);

        // actually call the static method to test
        URI uri = ShogunCoreContextUtil.getApplicationURIFromRequest(request);

        String expected = scheme + "://" + host + ":" + port + path;
        String actual = uri.toString();

        assertEquals(expected, actual);

    }

    @Test
    public void testInstantiation() {
        assertNotNull(new ShogunCoreContextUtil());
    }

}
