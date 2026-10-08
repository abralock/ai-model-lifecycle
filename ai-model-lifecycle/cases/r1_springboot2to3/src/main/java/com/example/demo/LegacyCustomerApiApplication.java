package com.example.demo;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

/** Application entry point (Spring Boot 2.7, javax.* era). */
@SpringBootApplication
@EnableJpaRepositories
public class LegacyCustomerApiApplication {
    public static void main(String[] args) {
        SpringApplication.run(LegacyCustomerApiApplication.class, args);
    }
}
