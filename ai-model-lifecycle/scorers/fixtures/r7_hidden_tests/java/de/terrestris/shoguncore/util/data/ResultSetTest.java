package de.terrestris.shoguncore.util.data;

import org.junit.jupiter.api.Test;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

/**
 * @author Marc Jansen
 */
public class ResultSetTest {

    private final static String KEY_SUCCESS = "success";
    private final static String KEY_DATA = "data";
    private final static String KEY_TOTAL = "total";
    private final static String KEY_MESSAGE = "message";

    private final static Collection<String> KEYS_ALWAYS_EXISTING = Arrays.asList(KEY_SUCCESS);
    private final static Collection<String> KEYS_ONLY_SUCCESS = Arrays.asList(KEY_DATA, KEY_TOTAL);
    private final static Collection<String> KEYS_ONLY_ERROR = Arrays.asList(KEY_MESSAGE);

    @Test
    public void testSuccessWithSet() {
        Set<String> data = new HashSet<String>();
        data.add("Humpty");
        data.add("Dumpty");
        Map<String, Object> resultSet = ResultSet.success(data);

        assertNotNull(resultSet, "Set does not become null");
        makeSuccessFieldAssertions(resultSet, data);
    }

    @Test
    public void testSuccessWithList() {
        List<String> data = Arrays.asList("foo", "bar", "baz");
        Map<String, Object> resultSet = ResultSet.success(data);

        assertNotNull(resultSet, "List does not become null");
        makeSuccessFieldAssertions(resultSet, data);
    }

    @Test
    public void testSuccessWithSomeObject() {
        Object data = "I am an object!";
        Map<String, Object> resultSet = ResultSet.success(data);

        assertNotNull(resultSet, "Object does not become null");
        makeSuccessFieldAssertions(resultSet, data);
    }

    @Test
    public void testSuccessWithNull() {
        Map<String, Object> resultSet = ResultSet.success(null);

        assertNotNull(resultSet, "'null' does not become null");
        makeSuccessFieldAssertions(resultSet, null);
    }

    @Test
    public void testErrorWithMessage() {
        Map<String, Object> resultSet = ResultSet.error("My error message");

        assertNotNull(resultSet, "Message does not become null");
        makeErrorFieldAssertions(resultSet);
    }

    @Test
    public void testErrorWithMessageAndAdditionalInfo() {
        final String additionalInfoKey = "additionalInfo";
        final String testKey = "foo";
        final String testValue = "bar";
        final Map<String, Object> testMap = new HashMap<>();
        testMap.put(testKey, testValue);
        Map<String, Object> resultSet = ResultSet.error("My error message", testMap);

        assertNotNull(resultSet, "Result does not become null");
        makeErrorFieldAssertions(resultSet);

        final Object additionalInfoMapObj = resultSet.get(additionalInfoKey);
        assertNotNull(additionalInfoMapObj, "Value for key '" + additionalInfoKey + "' is defined");
        assertTrue(additionalInfoMapObj instanceof Map, "Additional info is an instance of map");

        final Map additionalInfoMap = (Map) additionalInfoMapObj;
        assertEquals(additionalInfoMap.get(testKey), testValue, "Provided additional info matches returned one");
    }


    private void makeSuccessFieldAssertions(Map<String, Object> resultSet, Object expectedData) {
        Set<String> expectedKeys = new HashSet<String>(KEYS_ALWAYS_EXISTING);
        expectedKeys.addAll(KEYS_ONLY_SUCCESS);

        for (String expectedKey : expectedKeys) {
            assertTrue(resultSet.containsKey(expectedKey), "Expected key '" + expectedKey + "'");
        }
        assertTrue((boolean) resultSet.get(KEY_SUCCESS), "Key '" + KEY_SUCCESS + "' is true");
        assertTrue((int) resultSet.get(KEY_TOTAL) >= 0, "Key '" + KEY_TOTAL + "' is >= 0");
        assertEquals(resultSet.get(KEY_DATA), expectedData);
    }

    private void makeErrorFieldAssertions(Map<String, Object> resultSet) {
        Set<String> expectedKeys = new HashSet<String>(KEYS_ALWAYS_EXISTING);
        expectedKeys.addAll(KEYS_ONLY_ERROR);

        for (String expectedKey : expectedKeys) {
            assertTrue(resultSet.containsKey(expectedKey), "Expected key '" + expectedKey + "'");
        }
        assertFalse((boolean) resultSet.get(KEY_SUCCESS), "Key '" + KEY_SUCCESS + "' is false");
    }

    @Test
    public void testInstantiation() {
        assertNotNull(new ResultSet());
    }

}
