# Task: Upgrade a real Java library to Hibernate 6 and JUnit 5

The attached project is a real open-source framework: **SHOGun-Core**
(`de.terrestris:shogun-core`, 5.3.14-SNAPSHOT) by terrestris, the backend
library of a web-GIS platform: JPA entities with a second-level cache,
generic Hibernate DAOs, CRUD services with Spring Security ACL-style
permission evaluators, REST and web controllers, GeoServer interceptors
(WMS/WFS/WCS), mail, LDAP and token handling. It runs on **Java 8, Spring
Framework 5.3 (not Spring Boot), Spring Security 5.5, Hibernate ORM 5.4 and
JUnit 4 with PowerMock**.

Upgrade the `shogun-core-main` module (and the parent `pom.xml`) to:

* **Hibernate ORM 6.x** (6.4 or later) with **Jakarta Persistence 3.1**;
* **Spring Framework 6.x** and **Spring Security 6.x** (still not Spring Boot);
* **Java 17**;
* **JUnit Jupiter 5** for the project's tests: no JUnit 4 and no PowerMock.

The module `shogun-core-webapp-archetype` is out of scope: leave it unchanged
(it is not built or checked).

## Acceptance criteria (this is how your work is checked)

1. The build passes with Maven 3.8 and Java 17, from the project root:
   `mvn -B -pl shogun-core-main -am verify`.
2. **The project's own tests are migrated to JUnit 5 and pass.** Today
   `src/test` holds 56 test classes with **776 tests**, all passing (on Java 8).
   After your change, `mvn -pl shogun-core-main -am verify` must run at least
   776 tests with no failures, errors or skipped tests. Don't delete tests,
   and don't disable them (`@Disabled`, `@Ignore`, assumptions) or exclude them
   from the build. No JUnit 4 or PowerMock may remain in the tests or the
   poms: no `org.junit.Test`, `org.junit.Before`, `org.junit.runner.*`,
   `org.junit.Assert`, `org.powermock.*`, and no `junit:junit`,
   `junit-vintage-engine` or `powermock-*` dependency. Mockito 5 (with
   `mockito-inline` behaviour, which mocks static methods) is fine.
3. **The public API stays the same**, except for the replacement API below.
   Every public class, interface and method keeps its package
   (`de.terrestris.shoguncore.*`), name, parameter types and return type. Our
   own JUnit 5 migration of the same tests is also run against your `src/main`,
   in place of your `src/test`, so a renamed class or a changed signature fails.
   Two private members are also reached by the tests through reflection and
   must keep their names: the field `namespaceBoundUrl` and the method
   `getMostSpecificRule` of `GeoServerInterceptorService`.
4. No Jakarta EE API is still used through its old `javax.*` package in
   `src/main` or `src/test`: `javax.persistence`, `javax.servlet`,
   `javax.transaction`, `javax.annotation.Resource`/`PostConstruct`,
   `javax.mail`, `javax.validation`. Packages that did not move (`javax.xml.*`,
   `javax.naming`, `javax.imageio`, `javax.sql`) are fine.

## The replacement API for Hibernate's legacy Criteria

Hibernate 6 removes `org.hibernate.criterion` (`Criterion`, `Restrictions`,
`Order`, `Projections`, ...), which the DAO API uses today. Replace it with
exactly these two types, in package `de.terrestris.shoguncore.dao`:

```java
package de.terrestris.shoguncore.dao;

import jakarta.persistence.criteria.CriteriaBuilder;
import jakarta.persistence.criteria.CriteriaQuery;
import jakarta.persistence.criteria.Predicate;
import jakarta.persistence.criteria.Root;

/** One restriction of a DAO query, built with the JPA Criteria API. */
@FunctionalInterface
public interface QueryRestriction<E> {
    Predicate toPredicate(Root<E> root, CriteriaQuery<?> query, CriteriaBuilder cb);
}
```

```java
package de.terrestris.shoguncore.dao;

/** A sort order of a DAO query: a property name and a direction. */
public final class SortOrder {
    public static SortOrder asc(String property)  { ... }
    public static SortOrder desc(String property) { ... }
    public String getProperty()  { ... }
    public boolean isAscending() { ... }
}
```

Every public or protected DAO and service method that takes
`org.hibernate.criterion.Criterion...` takes `QueryRestriction<E>...` instead,
in the same position and with the same name, for example:

| Today (`GenericHibernateDao<E, ID>`) | After |
|---|---|
| `List<E> findByCriteria(Criterion... criterion)` | `List<E> findByCriteria(QueryRestriction<E>... restrictions)` |
| `E findByUniqueCriteria(Criterion... criterion)` | `E findByUniqueCriteria(QueryRestriction<E>... restrictions)` |
| `List<E> findByCriteriaRestricted(List<String> restrictFieldNames, Criterion... criterion)` | `List<E> findByCriteriaRestricted(List<String> restrictFieldNames, QueryRestriction<E>... restrictions)` |
| `PagingResult<E> findByCriteriaWithSortingAndPaging(Integer firstResult, Integer maxResults, List<Order> sorters, Criterion... criterion)` | `PagingResult<E> findByCriteriaWithSortingAndPaging(Integer firstResult, Integer maxResults, List<SortOrder> sorters, QueryRestriction<E>... restrictions)` |
| `Number getTotalCount(Criterion... criterion)` | `Number getTotalCount(QueryRestriction<E>... restrictions)` |
| `List<E> findAllWhereFieldEquals(String fieldName, Object fieldEntity, Criterion... criterion)` | `List<E> findAllWhereFieldEquals(String fieldName, Object fieldEntity, QueryRestriction<E>... restrictions)` |
| `List<E> findAllWithCollectionContaining(String fieldName, PersistentObject subElement, Criterion... criterion)` | `List<E> findAllWithCollectionContaining(String fieldName, PersistentObject subElement, QueryRestriction<E>... restrictions)` |

The behaviour stays the same: the restrictions are combined with AND; results
are distinct root entities; a `null` or empty array means no restriction;
`findByUniqueCriteria` returns `null` when nothing matches;
`findByCriteriaRestricted` returns entities with only the listed fields set
(all fields when the list is `null`); `getTotalCount` counts distinct entities
matching the restrictions. Overrides in subclasses (for example in `UserDao`)
and the callers in the services change the same way. Protected helpers that
build a legacy `Criteria` (`createDistinctRootEntityCriteria`) may change or
go: they are not part of the public API.

## Output format

Paths are relative to the project root (`pom.xml`, `shogun-core-main/...`),
not to the `project/` folder of the case listing.

For each file you change or create, emit it whole:

````
### FILE: shogun-core-main/src/main/java/de/terrestris/shoguncore/dao/QueryRestriction.java
```java
...full file content...
```
````

To remove a file, emit a single line `### DELETE: <path>`. Files you do not
mention stay exactly as they are. Do not add commentary outside these blocks.
