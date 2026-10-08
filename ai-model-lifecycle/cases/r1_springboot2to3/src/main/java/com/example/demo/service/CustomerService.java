package com.example.demo.service;

import com.example.demo.entity.Customer;
import com.example.demo.repo.CustomerRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.PostConstruct;
import javax.annotation.PreDestroy;
import java.util.List;
import java.util.Optional;

/**
 * Customer service. Uses javax.annotation.{PostConstruct,PreDestroy} — these must
 * become jakarta.annotation.* on the Boot 3.x migration (javax.annotation was
 * removed from the JDK / Spring 6).
 */
@Service
public class CustomerService {

    private final CustomerRepository repository;

    public CustomerService(CustomerRepository repository) {
        this.repository = repository;
    }

    @PostConstruct
    public void init() {
        // warm-up hook
    }

    @PreDestroy
    public void shutdown() {
        // cleanup hook
    }

    @Transactional(readOnly = true)
    public List<Customer> all() {
        return repository.findAll();
    }

    @Transactional(readOnly = true)
    public Optional<Customer> byEmail(String email) {
        return repository.findByEmail(email);
    }

    @Transactional
    public Customer create(String fullName, String email, String tier) {
        return repository.save(new Customer(fullName, email, tier));
    }
}
