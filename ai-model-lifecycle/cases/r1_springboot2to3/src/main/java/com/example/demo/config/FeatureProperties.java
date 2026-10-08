package com.example.demo.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

import javax.annotation.PostConstruct;

/** Feature flags bound from application properties. Uses javax.annotation.PostConstruct. */
@ConfigurationProperties(prefix = "app.features")
public class FeatureProperties {

    private boolean newPricing = false;
    private boolean auditLog = true;

    @PostConstruct
    public void validate() {
        // no-op validation hook
    }

    public boolean isNewPricing() {
        return newPricing;
    }

    public void setNewPricing(boolean newPricing) {
        this.newPricing = newPricing;
    }

    public boolean isAuditLog() {
        return auditLog;
    }

    public void setAuditLog(boolean auditLog) {
        this.auditLog = auditLog;
    }
}
