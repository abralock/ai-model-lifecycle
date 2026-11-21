package de.terrestris.shoguncore.security.access.factory;

import static org.hamcrest.CoreMatchers.instanceOf;
import static org.hamcrest.MatcherAssert.assertThat;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import de.terrestris.shoguncore.model.PersistentObject;
import de.terrestris.shoguncore.model.User;
import de.terrestris.shoguncore.security.access.entity.PersistentObjectPermissionEvaluator;
import de.terrestris.shoguncore.security.access.entity.UserPermissionEvaluator;

/**
 * @author Nils Bühner
 */
public class EntityPermissionEvaluatorFactoryTest {

    @SuppressWarnings("rawtypes")
    EntityPermissionEvaluatorFactory entityPermissionEvaluatorFactory;

    @BeforeEach
    public void setUp() {
        entityPermissionEvaluatorFactory = new EntityPermissionEvaluatorFactory<>();
    }

    @SuppressWarnings({"rawtypes", "unchecked"})
    @Test
    public void getEntityPermissionEvaluator_shouldReturnUserEvaluatorForUserClass() {
        Class<User> userClass = User.class;

        PersistentObjectPermissionEvaluator entityPermissionEvaluator = entityPermissionEvaluatorFactory
            .getEntityPermissionEvaluator(userClass);

        assertThat(entityPermissionEvaluator, instanceOf(UserPermissionEvaluator.class));
    }

    @SuppressWarnings({"rawtypes", "unchecked"})
    @Test
    public void getEntityPermissionEvaluator_shouldReturnDefaultEvaluatorForPersistentObjects() {
        Class<PersistentObject> persistentObjectClass = PersistentObject.class;

        PersistentObjectPermissionEvaluator entityPermissionEvaluator = entityPermissionEvaluatorFactory
            .getEntityPermissionEvaluator(persistentObjectClass);

        assertThat(entityPermissionEvaluator, instanceOf(PersistentObjectPermissionEvaluator.class));
    }


}
