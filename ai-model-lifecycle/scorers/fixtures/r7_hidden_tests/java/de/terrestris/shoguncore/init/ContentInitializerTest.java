package de.terrestris.shoguncore.init;

import de.terrestris.shoguncore.model.PersistentObject;
import de.terrestris.shoguncore.model.User;
import de.terrestris.shoguncore.model.interceptor.InterceptorRule;
import de.terrestris.shoguncore.service.InitializationService;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentMatchers;
import org.mockito.Mock;
import org.mockito.MockedStatic;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;

import java.util.LinkedList;
import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;

/**
 * Test class for {@link ContentInitializer}
 *
 * @author Andre Henn
 */
public class ContentInitializerTest {

    @Mock
    private Logger loggerMock;

    @Mock(name = "initializationService")
    private InitializationService initializationService;

    private ContentInitializer contentInitializer;

    private AutoCloseable mocks;

    private MockedStatic<LogManager> logManagerMock;

    @BeforeEach
    public void setUp(){
        mocks = MockitoAnnotations.openMocks(this);
        logManagerMock = Mockito.mockStatic(LogManager.class);
        logManagerMock.when(() -> LogManager.getLogger(any(Class.class))).
            thenReturn(loggerMock);
        contentInitializer = new ContentInitializer();
    }

    @AfterEach
    public void tearDown() throws Exception {
        logManagerMock.close();
        mocks.close();
    }

    @Test
    public void initializeDatabaseContent_doesNothingIfShogunInitDisabled () {
        contentInitializer.setShogunInitEnabled(false);
        contentInitializer.initializeDatabaseContent();

        verify(loggerMock).info("Not initializing anything for SHOGun.");
    }

    @Test
    public void initializeDatabaseContent_callsSaveUserIfPersistentObjectIsAnUser() {
        contentInitializer.setShogunInitEnabled(true);
        final List<PersistentObject> objToCreate = new LinkedList<>();
        objToCreate.add(new User("peter", "peter", "peter"));
        contentInitializer.setObjectsToCreate(objToCreate);
        contentInitializer.setInitService(this.initializationService);
        contentInitializer.initializeDatabaseContent();

        // should not be called since mapModuleId and layerIds are empty
        Mockito.verify(initializationService, Mockito.times(1)).
            saveUser(ArgumentMatchers.any(User.class)
            );
        Mockito.verify(initializationService,  Mockito.never()).
            savePersistentObject(ArgumentMatchers.any(PersistentObject.class)
            );
        Mockito.verifyNoMoreInteractions(initializationService);
    }

    @Test
    public void initializeDatabaseContent_callsSavePersistentObjectIfPersistentObjectIsNotAnUser() {
        contentInitializer.setShogunInitEnabled(true);
        final List<PersistentObject> objToCreate = new LinkedList<>();
        objToCreate.add(new InterceptorRule());
        contentInitializer.setObjectsToCreate(objToCreate);
        contentInitializer.setInitService(this.initializationService);
        contentInitializer.initializeDatabaseContent();

        // should not be called since mapModuleId and layerIds are empty
        Mockito.verify(initializationService, Mockito.never()).
            saveUser(ArgumentMatchers.any(User.class)
            );
        Mockito.verify(initializationService, Mockito.times(1)).
            savePersistentObject(ArgumentMatchers.any(InterceptorRule.class)
            );
        Mockito.verifyNoMoreInteractions(initializationService);
    }
}
