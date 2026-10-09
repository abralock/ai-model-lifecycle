package com.example.demo.service;

import com.example.demo.repo.CustomerRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.when;

import java.util.List;
import java.util.Optional;

/** JUnit 4 + Mockito test for CustomerService. Migrate to JUnit 5 + MockitoExtension. */
public class CustomerServiceTest {

    private CustomerRepository repository;
    private CustomerService service;

    @BeforeEach
    public void setUp() {
        repository = Mockito.mock(CustomerRepository.class);
        service = new CustomerService(repository);
    }

    @Test
    public void byEmailDelegatesToRepository() {
        when(repository.findByEmail("x@example.com"))
                .thenReturn(Optional.of(new com.example.demo.entity.Customer("X", "x@example.com", "GOLD")));

        Optional<com.example.demo.entity.Customer> result = service.byEmail("x@example.com");

        assertTrue(result.isPresent());
        assertEquals("X", result.get().getFullName());
    }

    @Test
    public void allReturnsRepositoryList() {
        when(repository.findAll()).thenReturn(List.of());
        assertEquals(0, service.all().size());
    }
}
