package de.terrestris.shoguncore.dao;

import de.terrestris.shoguncore.model.Application;
import de.terrestris.shoguncore.model.Person;
import de.terrestris.shoguncore.model.PersistentObject;
import de.terrestris.shoguncore.model.User;
import de.terrestris.shoguncore.model.UserGroup;
import de.terrestris.shoguncore.model.interceptor.InterceptorRule;
import de.terrestris.shoguncore.model.layer.source.ImageWmsLayerDataSource;
import de.terrestris.shoguncore.model.layer.source.LayerDataSource;
import de.terrestris.shoguncore.model.layer.source.WfsLayerDataSource;
import de.terrestris.shoguncore.model.security.Permission;
import de.terrestris.shoguncore.model.security.PermissionCollection;
import de.terrestris.shoguncore.util.enumeration.HttpEnum;
import de.terrestris.shoguncore.util.enumeration.InterceptorEnum;
import de.terrestris.shoguncore.util.enumeration.OgcEnum;
import jakarta.persistence.criteria.Root;
import org.hibernate.HibernateException;
import org.hibernate.SessionFactory;
import org.joda.time.DateTime;
import org.joda.time.LocalDate;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.test.annotation.Rollback;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit.jupiter.SpringExtension;
import org.springframework.transaction.annotation.Transactional;

import java.util.Arrays;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Tests the {@link QueryRestriction} / {@link SortOrder} based query methods
 * of the {@link GenericHibernateDao} (and some of its subclasses) against a
 * real (H2) database.
 */
@ExtendWith(SpringExtension.class)
@ContextConfiguration(locations = {"classpath*:META-INF/spring/test-context-dao.xml"})
@Transactional
@Rollback(true)
@SuppressWarnings("unchecked")
public class QueryRestrictionDaoTest {

    @Autowired
    private AppTestDao appDao;

    @Autowired
    @Qualifier("userDao")
    private UserDao<User> userDao;

    @Autowired
    @Qualifier("personDao")
    private PersonDao<Person> personDao;

    @Autowired
    @Qualifier("userGroupDao")
    private UserGroupDao<UserGroup> userGroupDao;

    @Autowired
    @Qualifier("permissionCollectionDao")
    private PermissionCollectionDao<PermissionCollection> permissionCollectionDao;

    @Autowired
    @Qualifier("interceptorRuleDao")
    private InterceptorRuleDao<InterceptorRule> interceptorRuleDao;

    @Autowired
    @Qualifier("layerDataSourceDao")
    private LayerDataSourceDao<LayerDataSource> layerDataSourceDao;

    @Autowired
    private SessionFactory sessionFactory;

    private static QueryRestriction<Application> nameEquals(String name) {
        return (root, query, cb) -> cb.equal(root.get("name"), name);
    }

    private Application saveApp(String name, String description) {
        Application app = new Application(name, description);
        appDao.saveOrUpdate(app);
        return app;
    }

    /**
     * Writes all changes to the database and clears the session, so that
     * entities have to be read from the database again. (The second level
     * cache entries of the entities are not used within the running
     * transaction, which will be rolled back.)
     */
    private void flushAndClear() {
        sessionFactory.getCurrentSession().flush();
        sessionFactory.getCurrentSession().clear();
    }

    @Test
    public void findByCriteria_combinesRestrictionsWithAnd() {
        saveApp("a", "x");
        Application ay = saveApp("a", "y");
        saveApp("b", "y");

        QueryRestriction<Application> descIsY = (root, query, cb) -> cb.equal(root.get("description"), "y");

        List<Application> result = appDao.findByCriteria(nameEquals("a"), descIsY);

        assertEquals(1, result.size());
        assertSame(ay, result.get(0));
    }

    @Test
    public void findByCriteria_treatsANullArrayAsNoRestriction() {
        saveApp("a", "x");
        saveApp("b", "y");

        // the prompt: "a `null` or empty array means no restriction"
        assertEquals(2, appDao.findByCriteria((QueryRestriction<Application>[]) null).size());
        assertEquals(2, appDao.findByCriteria().size());
    }

    @Test
    public void findByCriteria_returnsDistinctRootEntities() {
        Application app = saveApp("a", "x");
        Application otherApp = saveApp("b", "y");
        User user1 = new User("first", "last", "user1");
        User user2 = new User("first", "last", "user2");
        userDao.saveOrUpdate(user1);
        userDao.saveOrUpdate(user2);
        PermissionCollection read = new PermissionCollection(new HashSet<>(Collections.singletonList(Permission.READ)));
        PermissionCollection update = new PermissionCollection(new HashSet<>(Collections.singletonList(Permission.UPDATE)));
        permissionCollectionDao.saveOrUpdate(read);
        permissionCollectionDao.saveOrUpdate(update);
        app.getUserPermissions().put(user1, read);
        app.getUserPermissions().put(user2, update);
        otherApp.getUserPermissions().put(user1, read);
        appDao.saveOrUpdate(app);
        appDao.saveOrUpdate(otherApp);
        flushAndClear();

        // the join results in two rows for the first app
        QueryRestriction<Application> hasUserPermissions = (root, query, cb) -> cb.isNotNull(
            root.join("userPermissions").get("id"));

        List<Application> result = appDao.findByCriteria(hasUserPermissions);
        assertEquals(2, result.size());
        assertEquals(2, appDao.getTotalCount(hasUserPermissions).intValue());
    }

    @Test
    public void findByUniqueCriteria_returnsNullIfNothingMatches() {
        saveApp("a", "x");

        assertNull(appDao.findByUniqueCriteria(nameEquals("does not exist")));
    }

    @Test
    public void findByUniqueCriteria_returnsTheUniqueResult() {
        Application app = saveApp("a", "x");
        saveApp("b", "x");

        assertSame(app, appDao.findByUniqueCriteria(nameEquals("a")));
    }

    @Test
    public void findByUniqueCriteria_throwsIfResultIsNotUnique() {
        saveApp("a", "x");
        saveApp("a", "y");

        assertThrows(HibernateException.class, () -> appDao.findByUniqueCriteria(nameEquals("a")));
    }

    @Test
    public void findByCriteriaRestricted_setsOnlyTheRequestedFields() {
        saveApp("a", "x");
        saveApp("b", "y");

        List<Application> result = appDao.findByCriteriaRestricted(Arrays.asList("id", "name"), nameEquals("a"));

        assertEquals(1, result.size());
        Application restricted = result.get(0);
        assertNotNull(restricted.getId());
        assertEquals("a", restricted.getName());
        assertNull(restricted.getDescription());
    }

    @Test
    public void findByCriteriaRestricted_returnsFullEntitiesWithoutFieldNames() {
        Application app = saveApp("a", "x");
        saveApp("b", "y");

        List<Application> result = appDao.findByCriteriaRestricted(null, nameEquals("a"));

        assertEquals(1, result.size());
        assertSame(app, result.get(0));
        assertEquals(2, appDao.findByCriteriaRestricted(null).size());
    }

    @Test
    public void getTotalCount_countsTheMatchingEntities() {
        saveApp("a", "x");
        saveApp("a", "y");
        saveApp("b", "y");

        assertEquals(3L, appDao.getTotalCount());
        assertEquals(2L, appDao.getTotalCount(nameEquals("a")));
        assertEquals(0L, appDao.getTotalCount(nameEquals("c")));
    }

    @Test
    public void findByCriteriaWithSortingAndPaging_sortsByMultipleProperties() {
        Application a2 = saveApp("a", "2");
        Application b1 = saveApp("b", "1");
        Application a1 = saveApp("a", "1");

        List<SortOrder> sorters = Arrays.asList(SortOrder.asc("name"), SortOrder.desc("description"));

        List<Application> result = appDao.findByCriteriaWithSortingAndPaging(null, null, sorters).getResultList();

        assertEquals(Arrays.asList(a2, a1, b1), result);
    }

    @Test
    public void userDao_findsByAccountNameAndEmail() {
        User user = new User("first", "last", "peter");
        user.setEmail("peter@example.com");
        userDao.saveOrUpdate(user);
        User otherUser = new User("first", "last", "paul");
        otherUser.setEmail("paul@example.com");
        userDao.saveOrUpdate(otherUser);

        assertSame(user, userDao.findByAccountName("peter"));
        assertSame(user, userDao.findByEmail("peter@example.com"));
        assertNull(userDao.findByAccountName("mary"));
    }

    @Test
    public void findAllUserPermissionsOfUser_findsPermissionsOfAllEntityTypes() {
        User user = new User("first", "last", "peter");
        User otherUser = new User("first", "last", "paul");
        userDao.saveOrUpdate(user);
        userDao.saveOrUpdate(otherUser);

        PermissionCollection read = new PermissionCollection(new HashSet<>(Collections.singletonList(Permission.READ)));
        permissionCollectionDao.saveOrUpdate(read);

        Application app = saveApp("a", "x");
        app.getUserPermissions().put(user, read);
        appDao.saveOrUpdate(app);

        UserGroup group = new UserGroup();
        group.setName("group");
        group.getUserPermissions().put(user, read);
        group.getGroupPermissions().put(group, read);
        userGroupDao.saveOrUpdate(group);

        Application appOfOtherUser = saveApp("b", "y");
        appOfOtherUser.getUserPermissions().put(otherUser, read);
        appDao.saveOrUpdate(appOfOtherUser);

        flushAndClear();

        User reloadedUser = userDao.findByAccountName("peter");
        Map<PersistentObject, PermissionCollection> permissions = appDao.findAllUserPermissionsOfUser(reloadedUser);

        assertEquals(2, permissions.size());
        assertTrue(permissions.keySet().stream().anyMatch(e -> e instanceof Application && "a".equals(((Application) e).getName())));
        assertTrue(permissions.keySet().stream().anyMatch(e -> e instanceof UserGroup));
        permissions.values().forEach(pc -> assertEquals(Collections.singleton(Permission.READ), pc.getPermissions()));

        UserGroup reloadedGroup = userGroupDao.findById(group.getId());
        Map<PersistentObject, PermissionCollection> groupPermissions =
            appDao.findAllUserGroupPermissionsOfUserGroup(reloadedGroup);
        assertEquals(1, groupPermissions.size());
        assertSame(reloadedGroup, groupPermissions.keySet().iterator().next());
    }

    @Test
    public void interceptorRuleDao_findsRulesOrderedByEndPointAndOperation() {
        InterceptorRule generic = new InterceptorRule(HttpEnum.EventType.REQUEST, InterceptorEnum.RuleType.ALLOW,
            OgcEnum.ServiceType.WMS, null, null);
        InterceptorRule operation = new InterceptorRule(HttpEnum.EventType.REQUEST, InterceptorEnum.RuleType.DENY,
            OgcEnum.ServiceType.WMS, OgcEnum.OperationType.GET_MAP, null);
        InterceptorRule endPoint = new InterceptorRule(HttpEnum.EventType.REQUEST, InterceptorEnum.RuleType.MODIFY,
            OgcEnum.ServiceType.WMS, OgcEnum.OperationType.GET_MAP, "shogun:layer");
        InterceptorRule response = new InterceptorRule(HttpEnum.EventType.RESPONSE, InterceptorEnum.RuleType.ALLOW,
            OgcEnum.ServiceType.WMS, null, null);
        InterceptorRule wfs = new InterceptorRule(HttpEnum.EventType.REQUEST, InterceptorEnum.RuleType.ALLOW,
            OgcEnum.ServiceType.WFS, null, null);
        for (InterceptorRule rule : Arrays.asList(generic, operation, endPoint, response, wfs)) {
            interceptorRuleDao.saveOrUpdate(rule);
        }

        List<InterceptorRule> rules = interceptorRuleDao.findAllRulesForServiceAndEvent("WMS", "REQUEST");

        assertEquals(3, rules.size());
        assertSame(endPoint, rules.get(0));
        assertTrue(rules.containsAll(Arrays.asList(generic, operation)));
    }

    @Test
    public void restrictionsCanUseAttributesOfSubtypes() {
        ImageWmsLayerDataSource requestable = new ImageWmsLayerDataSource("wms", "ImageWMS", "http://example.com",
            "image/png", 256, 256, "1.1.1", "shogun:layer", "");
        requestable.setRequestableByPath(true);
        requestable.setCustomRequestPath("my-endpoint");
        ImageWmsLayerDataSource notRequestable = new ImageWmsLayerDataSource("wms", "ImageWMS", "http://example.com",
            "image/png", 256, 256, "1.1.1", "shogun:other", "");
        notRequestable.setRequestableByPath(false);
        notRequestable.setCustomRequestPath("my-endpoint");
        layerDataSourceDao.saveOrUpdate(requestable);
        layerDataSourceDao.saveOrUpdate(notRequestable);
        layerDataSourceDao.saveOrUpdate(new WfsLayerDataSource());
        flushAndClear();

        QueryRestriction<LayerDataSource> where = (root, query, cb) -> {
            Root<ImageWmsLayerDataSource> source = cb.treat(root, ImageWmsLayerDataSource.class);
            return cb.and(
                cb.equal(source.get("requestableByPath"), true),
                cb.equal(source.get("customRequestPath"), "my-endpoint")
            );
        };

        List<LayerDataSource> result = layerDataSourceDao.findByCriteria(where);

        assertEquals(1, result.size());
        assertEquals("shogun:layer", ((ImageWmsLayerDataSource) result.get(0)).getLayerNames());
    }

    @Test
    public void jodaTypesAreReadFromTheDatabase() {
        Person person = new Person("first", "last");
        person.setBirthday(new LocalDate(1980, 2, 29));
        personDao.saveOrUpdate(person);
        DateTime modified = new DateTime(person.getModified());

        flushAndClear();

        Person reloaded = personDao.findById(person.getId());
        assertEquals(new LocalDate(1980, 2, 29), reloaded.getBirthday());
        assertEquals(modified.getMillis(), reloaded.getModified().getMillis());
        assertEquals(person.getCreated().getMillis(), reloaded.getCreated().getMillis());
    }

    @Test
    public void loadByIdAndUnproxyReturnTheEntity() {
        Application app = saveApp("a", "x");
        flushAndClear();

        Application proxy = appDao.loadById(app.getId());
        Application unproxied = appDao.unproxy(proxy);

        assertEquals(Application.class, unproxied.getClass());
        assertEquals("a", unproxied.getName());
    }
}
