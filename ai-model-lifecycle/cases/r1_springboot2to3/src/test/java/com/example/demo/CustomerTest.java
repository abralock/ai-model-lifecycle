package com.example.demo;

import com.example.demo.entity.Customer;
import org.junit.Test;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;

/** JUnit 4 test — must be migrated to JUnit 5 (Jupiter) on the Boot 3.x upgrade. */
public class CustomerTest {

    @Test
    public void constructorSetsFields() {
        Customer c = new Customer("Ada Lovelace", "ada@example.com", "GOLD");
        assertEquals("Ada Lovelace", c.getFullName());
        assertEquals("ada@example.com", c.getEmail());
        assertEquals("GOLD", c.getTier());
        assertNotNull("createdAt should be set", c.getCreatedAt());
    }

    @Test
    public void settersWork() {
        Customer c = new Customer();
        c.setFullName("Grace Hopper");
        c.setEmail("grace@example.com");
        c.setTier("SILVER");
        assertEquals("Grace Hopper", c.getFullName());
        assertEquals("SILVER", c.getTier());
    }
}
