package de.terrestris.shoguncore.web;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.module.jsonSchema.JsonSchema;
import com.fasterxml.jackson.module.jsonSchema.JsonSchemaGenerator;
import de.terrestris.shoguncore.service.ModelDescriptionService;
import de.terrestris.shoguncore.util.data.ResultSet;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentMatchers;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

/**
 * Test for {@link ModelDescriptionController}
 *
 * @author Andre Henn
 */
public class ModelDescriptionControllerTest {

    private MockMvc mockMvc;

    @Mock(name = "modelDescriptionService")
    private ModelDescriptionService modelDescriptionService;

    @BeforeEach
    public void setup() {
        // Process mock annotations
        MockitoAnnotations.openMocks(this);

        ModelDescriptionController modelDescriptionController = new ModelDescriptionController();
        modelDescriptionController.setModelDescriptionService(modelDescriptionService);

        // Setup Spring test in standalone mode
        this.mockMvc = MockMvcBuilders.standaloneSetup(modelDescriptionController).build();
    }

    @Test
    public void getJsonSchemaSuccessMap() throws Exception {
        final String className = "Module";
        final Class<?> foundClass = Class.forName("de.terrestris.shoguncore.model.module.".concat(className));
        final JsonSchemaGenerator schemaGen = new JsonSchemaGenerator(new ObjectMapper());
        final JsonSchema schema = schemaGen.generateSchema(foundClass);

        Mockito.when(modelDescriptionService.getJsonSchema(
                ArgumentMatchers.any(String.class))
        ).thenReturn(schema);

        String MODELDESCRIPTION_ENDPOINT = "/describeModel/asJson/"+className+".action";

        MvcResult result = mockMvc.perform(MockMvcRequestBuilders.get(MODELDESCRIPTION_ENDPOINT)
                .param("className", className))
                .andExpect(MockMvcResultMatchers.status().isOk()).andReturn();

        String content = result.getResponse().getContentAsString();
        ObjectMapper objectMapper = new ObjectMapper();
        Assertions.assertEquals(objectMapper.writeValueAsString(ResultSet.success(schema)), content, "Returned body matched mocked one.");

        Mockito.verify(modelDescriptionService, Mockito.times(1)).
                getJsonSchema(ArgumentMatchers.any(String.class));
        Mockito.verifyNoMoreInteractions(modelDescriptionService);
    }

    @Test
    public void getJsonSchemaErrorMap() throws Exception {
        final String className = "Module";
        final String errorMsg = "Model description (json) for model " + className + " is null.";

        Mockito.when(modelDescriptionService.getJsonSchema(
                ArgumentMatchers.any(String.class))
        ).thenReturn(null);

        String MODELDESCRIPTION_ENDPOINT = "/describeModel/asJson/"+className+".action";

        MvcResult result = mockMvc.perform(MockMvcRequestBuilders.get(MODELDESCRIPTION_ENDPOINT)
                .param("className", className))
                .andExpect(MockMvcResultMatchers.status().isOk()).andReturn();

        String content = result.getResponse().getContentAsString();
        ObjectMapper objectMapper = new ObjectMapper();
        Assertions.assertEquals(objectMapper.writeValueAsString(ResultSet.error(errorMsg)), content, "Returned body matched mocked one.");

        Mockito.verify(modelDescriptionService, Mockito.times(1)).
                getJsonSchema(ArgumentMatchers.any(String.class));
        Mockito.verifyNoMoreInteractions(modelDescriptionService);
    }

}
