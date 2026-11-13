package de.terrestris.shoguncore.service;

import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoMoreInteractions;
import static org.mockito.Mockito.when;

import org.hibernate.HibernateException;
import de.terrestris.shoguncore.dao.QueryRestriction;
import org.junit.jupiter.api.Test;

import de.terrestris.shoguncore.dao.RoleDao;
import de.terrestris.shoguncore.model.Role;

public class RoleServiceTest extends PermissionAwareCrudServiceTest<Role, RoleDao<Role>, RoleService<Role, RoleDao<Role>>> {

    /**
     * @throws Exception
     */
    public void setUpImplToTest() throws Exception {
        implToTest = new Role();
    }

    @Override
    protected RoleService<Role, RoleDao<Role>> getCrudService() {
        return new RoleService<Role, RoleDao<Role>>();
    }

    @Test
    public void findByRoleName_shouldFindAsExpected() {
        String roleName = "ROLE_TEST";

        Role expectedRole = new Role(roleName);

        // mock the dao
        when(dao.findByUniqueCriteria(any(QueryRestriction.class))).thenReturn(expectedRole);

        Role actualRole = crudService.findByRoleName(roleName);

        verify(dao, times(1)).findByUniqueCriteria(any(QueryRestriction.class));
        verifyNoMoreInteractions(dao);

        assertEquals(expectedRole, actualRole);
    }

    @Test
    public void findByRoleName_shouldFindNothing() {
        String roleName = "ROLE_THAT_NOT_EXISTS";

        Role expectedRole = null;

        // mock the dao
        when(dao.findByUniqueCriteria(any(QueryRestriction.class))).thenReturn(expectedRole);

        Role actualRole = crudService.findByRoleName(roleName);

        verify(dao, times(1)).findByUniqueCriteria(any(QueryRestriction.class));
        verifyNoMoreInteractions(dao);

        assertEquals(expectedRole, actualRole);
    }

    @Test
    public void findByRoleName_shouldThrowHibernateException() {
        String roleName = "ROLE_THAT_THROWS_EXCEPTION";

        // mock the dao
        doThrow(new HibernateException("errormsg"))
            .when(dao).findByUniqueCriteria(any(QueryRestriction.class));

        assertThrows(HibernateException.class, () -> crudService.findByRoleName(roleName));

        verify(dao, times(1)).findByUniqueCriteria(any(QueryRestriction.class));
        verifyNoMoreInteractions(dao);
    }

    @SuppressWarnings("unchecked")
    @Override
    protected Class<RoleDao<Role>> getDaoClass() {
        return (Class<RoleDao<Role>>) new RoleDao<Role>().getClass();
    }

}
