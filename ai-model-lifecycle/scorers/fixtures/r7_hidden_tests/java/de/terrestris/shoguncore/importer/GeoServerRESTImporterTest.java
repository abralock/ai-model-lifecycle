package de.terrestris.shoguncore.importer;

import de.terrestris.shoguncore.importer.communication.RESTLayer;
import de.terrestris.shoguncore.util.http.HttpUtil;
import de.terrestris.shoguncore.util.model.Response;
import org.apache.http.HttpException;
import org.apache.http.entity.ContentType;
import org.junit.jupiter.api.Test;
import org.mockito.MockedStatic;
import org.mockito.Mockito;
import org.springframework.http.HttpStatus;

import java.net.URI;
import java.net.URISyntaxException;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;

/**
 * @author Andre Henn
 */
public class GeoServerRESTImporterTest {

    private GeoServerRESTImporter geoServerRESTImporter;

    public GeoServerRESTImporterTest() throws URISyntaxException {
        geoServerRESTImporter = new GeoServerRESTImporter("testURI/", "testuser", "testpasswd");
    }

    @Test
    public void updateLayerForImportTask_unsuccessful() throws Exception {
        final RESTLayer entity = new RESTLayer();
        boolean result = this.geoServerRESTImporter.updateLayerForImportTask(-1, -1, entity);
        assertFalse(result, "Either task ID or import job ID is not valid");

        result = this.geoServerRESTImporter.updateLayerForImportTask(5, 33, null);
        assertFalse(result, "Entity to update is null");
    }

    @Test
    public void updateLayerForImportTask_successful() throws URISyntaxException, HttpException {
        try (MockedStatic<HttpUtil> httpUtil = Mockito.mockStatic(HttpUtil.class)) {
            Response resp = new Response();
            resp.setStatusCode(HttpStatus.NO_CONTENT);

            httpUtil.when(() -> HttpUtil.put(
                    any(URI.class),
                    any(String.class),
                    any(ContentType.class),
                    any(String.class),
                    any(String.class))
            ).thenReturn(resp);

            final RESTLayer entity = new RESTLayer();
            boolean result = this.geoServerRESTImporter.updateLayerForImportTask(19, 9, entity);
            assertTrue(result, "HTTP post was not successful.");
        }
    }
}
