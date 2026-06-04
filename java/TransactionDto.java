package com.tdfraud.dto;

// DTOs (Data Transfer Objects) for the TD Fraud Analytics API
// Demonstrates: Java records (Java 16+), immutable data structures,
// clean separation between domain models and API responses

import java.time.LocalDate;
import java.util.Map;

// ── Transaction DTO ────────────────────────────────────────────────────────
public record TransactionDto(
    String      transactionId,
    String      customerId,
    LocalDate   transactionDate,
    String      transactionType,
    String      channel,
    double      amountCad,
    String      counterpartyCountry,
    boolean     isFlagged,
    String      flagReason,       // null if not flagged
    boolean     isHighRiskJurisdiction
) {}
