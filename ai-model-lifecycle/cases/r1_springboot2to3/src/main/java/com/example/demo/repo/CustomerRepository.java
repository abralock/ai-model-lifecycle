package com.example.demo.repo;

import com.example.demo.entity.Customer;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/** Spring Data JPA repository (unchanged API across Boot 2.7 -> 3.x). */
@Repository
public interface CustomerRepository extends JpaRepository<Customer, Long> {

    Optional<Customer> findByEmail(String email);

    List<Customer> findByTier(String tier);

    @Query("select c from Customer c where c.tier = :tier and c.fullName like %:name%")
    List<Customer> search(@Param("tier") String tier, @Param("name") String name);
}
