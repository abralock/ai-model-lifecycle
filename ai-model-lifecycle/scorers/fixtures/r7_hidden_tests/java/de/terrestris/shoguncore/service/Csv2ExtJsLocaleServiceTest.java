package de.terrestris.shoguncore.service;

import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.containsString;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Map;
import java.util.Set;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.test.context.ContextConfiguration;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.test.context.junit.jupiter.SpringExtension;

/**
 * @author Nils Bühner
 */
@ExtendWith(SpringExtension.class)
@ContextConfiguration(locations = {"classpath*:META-INF/spring/test-locale.xml"})
public class Csv2ExtJsLocaleServiceTest {

    @Autowired
    protected Csv2ExtJsLocaleService csv2localeService;

    private static final String CSV_TEST = "test";

    private static final String CSV_NONEXISTING = "nonexistingcsv";

    private static final String CSV_EMPTY = "empty";

    private static final String CSV_INVALID = "invalid";

    private static final String CSV_COL_COMPONENT_EMPTY = "component_empty";

    private static final String CSV_COL_FIELD_EMPTY = "field_empty";

    private static final String CSV_COL_FIELD_UNSUPPORTED_ARRAY = "field_unsupported_array";

    private static final String LOCALE_DE = "de";

    private static final String LOCALE_FR = "fr";

    /**
     * @throws Exception
     */
    @SuppressWarnings("unchecked")
    @Test
    public void workAsExpected() throws Exception {

        Map<String, Object> resultMap = csv2localeService.getAllComponentsForLocale(CSV_TEST, LOCALE_DE);

        final Set<String> keySet = resultMap.keySet();

        assertEquals(3, keySet.size());

        final String someCmpKey = "MyProject.some.Component";
        final String anotherCmpKey = "MyProject.another.Component";
        final String yetAnotherCmpKey = "MyProject.yet.another.Component";

        assertTrue(resultMap.containsKey(someCmpKey));
        assertTrue(resultMap.containsKey(anotherCmpKey));
        assertTrue(resultMap.containsKey(yetAnotherCmpKey));

        // "MyProject.some.Component"
        Map<String, Object> someCmpVal = (Map<String, Object>) resultMap.get(someCmpKey);
        assertEquals(1, someCmpVal.keySet().size());

        Map<String, Object> someCmpValConfig = (Map<String, Object>) someCmpVal.get("config");
        assertEquals(1, someCmpValConfig.keySet().size());

        Map<String, Object> someCmpValConfigData = (Map<String, Object>) someCmpValConfig.get("data");
        assertEquals(3, someCmpValConfigData.keySet().size());

        assertEquals("de:title;and something after a semicolon", someCmpValConfigData.get("title"));
        assertEquals("de:tooltip", someCmpValConfigData.get("tooltip"));
        assertEquals("{0} Zeile(n) ausgewählt", someCmpValConfigData.get("dragText"));

        // "MyProject.another.Component"
        Map<String, Object> anotherCmpVal = (Map<String, Object>) resultMap.get(anotherCmpKey);
        assertEquals(2, anotherCmpVal.keySet().size());
        assertEquals("de:foo", anotherCmpVal.get("justonefield"));

        Map<String, Object> anotherCmpValData = (Map<String, Object>) anotherCmpVal.get("data");
        assertEquals(2, anotherCmpValData.keySet().size());
        assertEquals("de:data.a", anotherCmpValData.get("a"));
        assertEquals("de:data.b", anotherCmpValData.get("b"));

        // "MyProject.yet.another.Component"
        Map<String, Object> yetAnotherCmpVal = (Map<String, Object>) resultMap.get(yetAnotherCmpKey);
        assertEquals(1, yetAnotherCmpVal.keySet().size());

        Map<String, Object> yetAnotherCmpValConfig = (Map<String, Object>) yetAnotherCmpVal.get("config");
        assertEquals(1, yetAnotherCmpValConfig.keySet().size());

        String[] yetAnotherCmpValConfigArray = (String[]) yetAnotherCmpValConfig.get("myArray");
        assertEquals(4, yetAnotherCmpValConfigArray.length);

        assertEquals("de:v1", yetAnotherCmpValConfigArray[0]);
        assertEquals("v2", yetAnotherCmpValConfigArray[1]);
        assertEquals("v3", yetAnotherCmpValConfigArray[2]);
        assertEquals(" ...", yetAnotherCmpValConfigArray[3]);

    }

    /**
     * @throws Exception
     */
    @Test
    public void throwExceptionWhenCsvResourceDoesNotExist() throws Exception {
        Exception exception = assertThrows(Exception.class,
            () -> csv2localeService.getAllComponentsForLocale(CSV_NONEXISTING, LOCALE_DE));
        assertThat(exception.getMessage(), containsString("CSV locale resource for " + CSV_NONEXISTING + " does not exist."));
    }

    /**
     * @throws Exception
     */
    @Test
    public void throwExceptionWhenCsvResourceIsEmpty() throws Exception {
        Exception exception = assertThrows(Exception.class,
            () -> csv2localeService.getAllComponentsForLocale(CSV_EMPTY, LOCALE_DE));
        assertThat(exception.getMessage(), containsString("CSV locale file seems to be empty."));
    }

    /**
     * @throws Exception
     */
    @Test
    public void throwExceptionWhenCsvResourceIsInvalid() throws Exception {
        Exception exception = assertThrows(Exception.class,
            () -> csv2localeService.getAllComponentsForLocale(CSV_INVALID, LOCALE_DE));
        assertThat(exception.getMessage(), containsString("CSV locale file is invalid: Not enough columns."));
    }

    /**
     * @throws Exception
     */
    @Test
    public void throwExceptionWhenCsvResourceIsMissingRequestedLocale() throws Exception {
        Exception exception = assertThrows(Exception.class,
            () -> csv2localeService.getAllComponentsForLocale(CSV_TEST, LOCALE_FR));
        assertThat(exception.getMessage(), containsString("Could not find locale " + LOCALE_FR + " in CSV file"));
    }

    /**
     * @throws Exception
     */
    @Test
    public void throwExceptionWhenCsvResourceIsMissingComponentEntry() throws Exception {
        Exception exception = assertThrows(Exception.class,
            () -> csv2localeService.getAllComponentsForLocale(CSV_COL_COMPONENT_EMPTY, LOCALE_DE));
        assertThat(exception.getMessage(), containsString("Missing component entry in CSV line " + 3));
    }

    /**
     * @throws Exception
     */
    @Test
    public void throwExceptionWhenCsvResourceIsMissingFieldEntry() throws Exception {
        Exception exception = assertThrows(Exception.class,
            () -> csv2localeService.getAllComponentsForLocale(CSV_COL_FIELD_EMPTY, LOCALE_DE));
        assertThat(exception.getMessage(), containsString("Missing field entry in CSV line " + 3));
    }

    /**
     * @throws Exception
     */
    @Test
    public void throwExceptionWhenCsvResourceContainsUnsupportedArrayUsage() throws Exception {
        final String field = "config[].myArray[]";
        Exception exception = assertThrows(Exception.class,
            () -> csv2localeService.getAllComponentsForLocale(CSV_COL_FIELD_UNSUPPORTED_ARRAY, LOCALE_DE));
        assertThat(exception.getMessage(), containsString("Invalid field description '" + field
            + "': '[]' may only occure once at the end, but not before"));
    }

}
