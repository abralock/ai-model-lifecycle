package de.terrestris.shoguncore.service;

import de.terrestris.shoguncore.util.http.HttpUtil;
import de.terrestris.shoguncore.util.model.Response;
import org.apache.commons.lang3.StringUtils;
import org.apache.http.HttpException;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.MockedStatic;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import java.io.IOException;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.LinkedList;
import java.util.List;

/**
 * Tests for {@link HttpProxyService}
 *
 * @author Andre Henn
 * @author terrestris GmbH & Co. KG
 */
public class HttpProxyServiceTest {

    /**
     * The static mock of the {@link HttpUtil} (if any), will be closed after each test.
     */
    private MockedStatic<HttpUtil> httpUtilMock;

    @AfterEach
    public void closeStaticMocks() {
        if (httpUtilMock != null) {
            httpUtilMock.close();
            httpUtilMock = null;
        }
    }

    @InjectMocks
    private HttpProxyService proxyService;

    @BeforeEach
    public void setUp() {
        MockitoAnnotations.openMocks(this);

        final List<String> whiteList = new LinkedList<>();
        // only domainName will be checked in proxy
        whiteList.add("terrestris.de");
        whiteList.add("terrestris.de:443");
        whiteList.add("mundialis.de");
        this.proxyService.setProxyWhiteList(whiteList);
    }

    @Test
    public void proxy_returns_400_when_no_url_is_given() {
        final ResponseEntity responseEntity = proxyService.doProxy(null, null, null);
        Assertions.assertEquals(HttpStatus.BAD_REQUEST, responseEntity.getStatusCode(), "Returned Status code matched mocked one.");
        Assertions.assertEquals(HttpProxyService.ERR_MSG_400_NO_URL, responseEntity.getBody(), "Returned Status message matched");
    }

    @Test
    public void proxy_returns_400_when_baseUrl_is_empty() {
        HttpServletRequest mockedRequest = Mockito.mock(HttpServletRequest.class);
        final String baseUrl = StringUtils.EMPTY;
        final ResponseEntity responseEntity = proxyService.doProxy(mockedRequest, baseUrl, null);
        Assertions.assertEquals(HttpStatus.BAD_REQUEST, responseEntity.getStatusCode(), "Returned Status code matched mocked one.");
        Assertions.assertEquals(HttpProxyService.ERR_MSG_400_NO_URL, responseEntity.getBody(), "Returned Status message matched");
    }

    @Test
    public void proxy_returns_500_when_baseUrl_is_no_valid_URL() {
        HttpServletRequest mockedRequest = Mockito.mock(HttpServletRequest.class);
        final String baseUrl = "$$$$___S04___$$$$";
        final ResponseEntity responseEntity = proxyService.doProxy(mockedRequest, baseUrl, null);
        Assertions.assertEquals(HttpStatus.INTERNAL_SERVER_ERROR, responseEntity.getStatusCode(), "Returned Status code matched mocked one.");
        Assertions.assertEquals(HttpProxyService.ERR_MSG_500, responseEntity.getBody(), "Returned Status message matched");
    }

    @Test
    public void proxy_returns_502_when_baseUrl_is_not_in_URL_whitelist() {
        HttpServletRequest mockedRequest = Mockito.mock(HttpServletRequest.class);
        final String baseUrl = "https://unallowedHost.com/unallowedPath";

        final ResponseEntity responseEntity = proxyService.doProxy(mockedRequest, baseUrl, null);
        Assertions.assertEquals(HttpStatus.BAD_GATEWAY, responseEntity.getStatusCode(), "Returned Status code matched mocked one.");
        Assertions.assertEquals(HttpProxyService.ERR_MSG_502, responseEntity.getBody(), "Returned Status message matched");
    }

    @Test
    public void proxy_returns_405_for_unsupported_HTTP_methods() {
        // currently unsupported
        final HttpMethod[] unsupportedHttpMethods = new HttpMethod[]{
            HttpMethod.DELETE,
            HttpMethod.PUT,
            HttpMethod.HEAD,
            HttpMethod.PATCH,
            HttpMethod.TRACE,
            HttpMethod.OPTIONS
        };
        final String baseUrl = "https://www.terrestris.de/internet.txt";

        httpUtilMock = Mockito.mockStatic(HttpUtil.class);
        for (HttpMethod unsupportedHttpMethod : unsupportedHttpMethods) {
            HttpServletRequest mockedRequest = Mockito.mock(HttpServletRequest.class);
            Mockito.when(mockedRequest.getMethod()).thenReturn(unsupportedHttpMethod.name());
            final ResponseEntity responseEntity = proxyService.doProxy(mockedRequest, baseUrl, null);
            Assertions.assertEquals(HttpStatus.METHOD_NOT_ALLOWED, responseEntity.getStatusCode(), "Returned Status code matched mocked one.");
            Assertions.assertEquals(HttpProxyService.ERR_MSG_405, responseEntity.getBody(), "Returned Status message matched");
        }
    }

    @Test
    public void proxy_returns_200_for_allowed_GET_request() throws URISyntaxException, HttpException {
        HttpServletRequest mockedRequest = Mockito.mock(HttpServletRequest.class);
        httpUtilMock = Mockito.mockStatic(HttpUtil.class);
        final String internetContent = "THE INTERNET!";
        final String baseUrl = "https://www.terrestris.de/internet.txt";
        final URI baseUri = new URI(baseUrl);
        Response mockedRespone = Mockito.mock(Response.class);

        final HttpHeaders headers = new HttpHeaders();
        headers.add(HttpHeaders.CONTENT_TYPE, "text/plain");
        HttpStatus status = HttpStatus.OK;

        Mockito.when(mockedRespone.getHeaders()).thenReturn(headers);
        Mockito.when(mockedRespone.getBody()).thenReturn(internetContent.getBytes());
        Mockito.when(mockedRespone.getStatusCode()).thenReturn(status);
        httpUtilMock.when(() -> HttpUtil.isHttpGetRequest(mockedRequest)).thenReturn(true);
        httpUtilMock.when(() -> HttpUtil.forwardGet(baseUri, mockedRequest, false)).thenReturn(mockedRespone);

        final ResponseEntity responseEntity = proxyService.doProxy(mockedRequest, baseUrl, null);
        Assertions.assertEquals(HttpStatus.OK, responseEntity.getStatusCode(), "Returned Status code matched mocked one.");

        final byte[] responseBodyAsByteArray = (byte[]) responseEntity.getBody();
        Assertions.assertEquals(new String(responseBodyAsByteArray), internetContent, "Returned content matched mocked one.");
    }

    @Test
    public void proxy_returns_400_for_erroneous_GET_requests() throws URISyntaxException, HttpException {
        HttpServletRequest mockedRequest = Mockito.mock(HttpServletRequest.class);
        httpUtilMock = Mockito.mockStatic(HttpUtil.class);
        final String internetContent = "THE INTERNET!";
        final String baseUrl = "https://www.terrestris.de/internet.txt";
        final URI baseUri = new URI(baseUrl);
        Response mockedRespone = Mockito.mock(Response.class);
        final String msg = "ERROR";

        final HttpHeaders headers = new HttpHeaders();
        headers.add(HttpHeaders.CONTENT_TYPE, "text/plain");
        HttpStatus status = HttpStatus.OK;

        Mockito.when(mockedRespone.getHeaders()).thenReturn(headers);
        Mockito.when(mockedRespone.getBody()).thenReturn(internetContent.getBytes());
        Mockito.when(mockedRespone.getStatusCode()).thenReturn(status);
        httpUtilMock.when(() -> HttpUtil.isHttpGetRequest(mockedRequest)).thenReturn(true);
        httpUtilMock.when(() -> HttpUtil.forwardGet(baseUri, mockedRequest, false)).thenThrow(new HttpException(msg));

        final ResponseEntity responseEntity = proxyService.doProxy(mockedRequest, baseUrl, null);
        Assertions.assertEquals(HttpStatus.BAD_REQUEST, responseEntity.getStatusCode(), "Returned Status code matched mocked one.");
        Assertions.assertEquals(HttpProxyService.ERR_MSG_400_COMMON, responseEntity.getBody(), "Returned Status matched");
    }

    @Test
    public void proxy_returns_200_for_allowed_POST_request() throws URISyntaxException, HttpException {
        HttpServletRequest mockedRequest = Mockito.mock(HttpServletRequest.class);
        httpUtilMock = Mockito.mockStatic(HttpUtil.class);
        final String internetContent = "THE INTERNET!";
        final String baseUrl = "https://www.terrestris.de/endpointToPostAt";
        final URI baseUri = new URI(baseUrl);
        Response mockedRespone = Mockito.mock(Response.class);

        final HttpHeaders headers = new HttpHeaders();
        headers.add(HttpHeaders.CONTENT_TYPE, "text/plain");
        HttpStatus status = HttpStatus.OK;

        Mockito.when(mockedRespone.getHeaders()).thenReturn(headers);
        Mockito.when(mockedRespone.getBody()).thenReturn(internetContent.getBytes());
        Mockito.when(mockedRespone.getStatusCode()).thenReturn(status);
        httpUtilMock.when(() -> HttpUtil.isHttpGetRequest(mockedRequest)).thenReturn(false);
        httpUtilMock.when(() -> HttpUtil.isHttpPostRequest(mockedRequest)).thenReturn(true);
        httpUtilMock.when(() -> HttpUtil.forwardPost(baseUri, mockedRequest, false)).thenReturn(mockedRespone);

        final ResponseEntity responseEntity = proxyService.doProxy(mockedRequest, baseUrl, null);
        Assertions.assertEquals(HttpStatus.OK, responseEntity.getStatusCode(), "Returned Status code matched mocked one.");

        final byte[] responseBodyAsByteArray = (byte[]) responseEntity.getBody();
        Assertions.assertEquals(new String(responseBodyAsByteArray), internetContent, "Returned content matched mocked one.");
    }

    @Test
    public void proxy_returns_400_for_erroneous_POST_requests() throws URISyntaxException, HttpException {
        HttpServletRequest mockedRequest = Mockito.mock(HttpServletRequest.class);
        httpUtilMock = Mockito.mockStatic(HttpUtil.class);
        final String internetContent = "THE INTERNET!";
        final String baseUrl = "https://www.terrestris.de/internet.txt";
        final URI baseUri = new URI(baseUrl);
        Response mockedRespone = Mockito.mock(Response.class);
        final String msg = "ERROR";

        final HttpHeaders headers = new HttpHeaders();
        headers.add(HttpHeaders.CONTENT_TYPE, "text/plain");
        HttpStatus status = HttpStatus.OK;

        Mockito.when(mockedRespone.getHeaders()).thenReturn(headers);
        Mockito.when(mockedRespone.getBody()).thenReturn(internetContent.getBytes());
        Mockito.when(mockedRespone.getStatusCode()).thenReturn(status);
        httpUtilMock.when(() -> HttpUtil.isHttpGetRequest(mockedRequest)).thenReturn(false);
        httpUtilMock.when(() -> HttpUtil.isHttpPostRequest(mockedRequest)).thenReturn(true);
        httpUtilMock.when(() -> HttpUtil.forwardPost(baseUri, mockedRequest, false)).thenThrow(new HttpException(msg));

        final ResponseEntity responseEntity = proxyService.doProxy(mockedRequest, baseUrl, null);
        Assertions.assertEquals(HttpStatus.BAD_REQUEST, responseEntity.getStatusCode(), "Returned Status code matched mocked one.");
        Assertions.assertEquals(HttpProxyService.ERR_MSG_400_COMMON, responseEntity.getBody(), "Returned Status matched");
    }


    @Test
    public void proxy_returns_200_for_allowed_FormMultipartPost_request() throws URISyntaxException, HttpException, IOException, ServletException {
        HttpServletRequest mockedRequest = Mockito.mock(HttpServletRequest.class);
        httpUtilMock = Mockito.mockStatic(HttpUtil.class);
        final String internetContent = "THE INTERNET!";
        final String baseUrl = "https://www.terrestris.de/endpointToPostAt";
        final URI baseUri = new URI(baseUrl);
        Response mockedRespone = Mockito.mock(Response.class);

        final HttpHeaders headers = new HttpHeaders();
        headers.add(HttpHeaders.CONTENT_TYPE, "text/plain");
        HttpStatus status = HttpStatus.OK;

        Mockito.when(mockedRespone.getHeaders()).thenReturn(headers);
        Mockito.when(mockedRespone.getBody()).thenReturn(internetContent.getBytes());
        Mockito.when(mockedRespone.getStatusCode()).thenReturn(status);
        httpUtilMock.when(() -> HttpUtil.isHttpGetRequest(mockedRequest)).thenReturn(false);
        httpUtilMock.when(() -> HttpUtil.isHttpPostRequest(mockedRequest)).thenReturn(true);
        httpUtilMock.when(() -> HttpUtil.isFormMultipartPost(mockedRequest)).thenReturn(true);
        httpUtilMock.when(() -> HttpUtil.forwardFormMultipartPost(baseUri, mockedRequest, false)).thenReturn(mockedRespone);

        final ResponseEntity responseEntity = proxyService.doProxy(mockedRequest, baseUrl, null);
        Assertions.assertEquals(HttpStatus.OK, responseEntity.getStatusCode(), "Returned Status code matched mocked one.");

        final byte[] responseBodyAsByteArray = (byte[]) responseEntity.getBody();
        Assertions.assertEquals(new String(responseBodyAsByteArray), internetContent, "Returned content matched mocked one.");
    }

    @Test
    public void proxy_returns_400_for_erroneous_FormMultipartPost_requests() throws URISyntaxException, HttpException, IOException, ServletException {
        HttpServletRequest mockedRequest = Mockito.mock(HttpServletRequest.class);
        httpUtilMock = Mockito.mockStatic(HttpUtil.class);
        final String internetContent = "THE INTERNET!";
        final String baseUrl = "https://www.terrestris.de/internet.txt";
        final URI baseUri = new URI(baseUrl);
        Response mockedRespone = Mockito.mock(Response.class);
        final String msg = "ERROR";

        final HttpHeaders headers = new HttpHeaders();
        headers.add(HttpHeaders.CONTENT_TYPE, "text/plain");
        HttpStatus status = HttpStatus.OK;

        Mockito.when(mockedRespone.getHeaders()).thenReturn(headers);
        Mockito.when(mockedRespone.getBody()).thenReturn(internetContent.getBytes());
        Mockito.when(mockedRespone.getStatusCode()).thenReturn(status);
        httpUtilMock.when(() -> HttpUtil.isHttpGetRequest(mockedRequest)).thenReturn(false);
        httpUtilMock.when(() -> HttpUtil.isHttpPostRequest(mockedRequest)).thenReturn(true);
        httpUtilMock.when(() -> HttpUtil.isFormMultipartPost(mockedRequest)).thenReturn(true);
        httpUtilMock.when(() -> HttpUtil.forwardFormMultipartPost(baseUri, mockedRequest, false)).thenThrow(new HttpException(msg));

        final ResponseEntity responseEntity = proxyService.doProxy(mockedRequest, baseUrl, null);
        Assertions.assertEquals(HttpStatus.BAD_REQUEST, responseEntity.getStatusCode(), "Returned Status code matched mocked one.");
        Assertions.assertEquals(HttpProxyService.ERR_MSG_400_COMMON, responseEntity.getBody(), "Returned Status matched");
    }
}
